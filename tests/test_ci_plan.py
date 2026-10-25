"""CI selection and its merge gate must fail closed across events and failures."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
BASE = "a" * 40
spec = importlib.util.spec_from_file_location("ci_plan", ROOT / "scripts/ci_plan.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class CiPlanTests(unittest.TestCase):
    def focused(self, paths):
        return ci.make_plan(paths, baseline=BASE)

    def test_missing_proof_unknown_ownership_and_events_are_full(self):
        for paths in (None, [], ["README.md"], ["modules/apps/ghostty/_package.nix"]):
            self.assertEqual(ci.make_plan(paths)["mode"], "full")
        for path in ("flake.nix", "flake.lock", "docs/ARCHITECTURE.md", "scripts/ci_plan.py", "new.nix", "modules/apps/new/_home.nix"):
            self.assertEqual(self.focused([path])["mode"], "full")
        for event in ("workflow_dispatch", "merge_group", "workflow_call", "unknown"):
            self.assertTrue(ci.requires_full(event, "refs/heads/main"))
        self.assertTrue(ci.requires_full("push", "refs/tags/v1"))
        self.assertTrue(ci.requires_full("pull_request", "", True))
        self.assertFalse(ci.requires_full("pull_request", ""))

    def test_docs_require_proof_and_graph(self):
        plan = self.focused(["README.md", "docs/CI.md"])
        self.assertEqual(plan["mode"], "docs")
        self.assertFalse(plan["checks"] or plan["schema3"] or plan["hosts"] or plan["legacy"])
        ci.validate_plan(plan)

    def test_transitive_shared_application_selection_and_schema_variants(self):
        graph = ci.load_graph()
        self.assertIn("apps/ghostty", ci.closure(graph, 3, ["roles/developer"]))
        self.assertIn("apps/ghostty", ci.closure(graph, 3, ["roles/support"]))
        self.assertIn("providers/flatpak", ci.closure(graph, 2, ["apps/gradia"]))
        self.assertIn("providers/nixpkgs", ci.closure(graph, 3, ["apps/gradia"]))
        plan = self.focused(["modules/apps/ghostty/_package.nix"])
        self.assertEqual(set(plan["schema3"]), {"capabilities", "dell-mixed", "all"})
        self.assertIn("profile-generation", plan["checks"])
        self.assertNotIn("desktop-icons", plan["checks"])
        self.assertIn("workstation", plan["hosts"])
        self.assertEqual(set(plan["legacy"]), set(ci.LEGACY))

    def test_assets_and_changed_file_unions(self):
        paths = ["modules/capabilities/devops/_assets/rootfs/usr/share/finite/zsh/aliases.zsh",
                 "modules/hosts/models/dell-xps-9350/_assets/dell-ipu7.conf"]
        union = self.focused(paths)
        for group in ("schema3", "hosts", "legacy", "checks"):
            self.assertEqual(set(union[group]), set().union(*(self.focused([p])[group] for p in paths)))

    def test_graph_must_be_unchanged_validated_and_have_exact_green_base(self):
        plan = ci.make_plan(["README.md"])
        graph = ci.load_graph()
        with patch.object(ci, "baseline_green", return_value=False):
            self.assertEqual(ci.with_baseline(plan, BASE, "owner/repo")["mode"], "full")
        with patch.object(ci, "baseline_green", return_value=True), \
                patch.object(ci, "load_graph", return_value=graph), \
                patch.object(ci.subprocess, "check_output", return_value=json.dumps(graph)):
            self.assertEqual(ci.with_baseline(plan, BASE, "owner/repo")["mode"], "docs")
        for failure in (ValueError("stale"), OSError("missing")):
            with patch.object(ci, "baseline_green", return_value=True), patch.object(ci, "load_graph", side_effect=failure):
                self.assertEqual(ci.with_baseline(plan, BASE, "owner/repo")["mode"], "full")
        with patch.object(ci, "baseline_green", return_value=True), patch.object(ci, "load_graph", return_value=graph), \
                patch.object(ci.subprocess, "check_output", return_value='{}'):
            self.assertEqual(ci.with_baseline(plan, BASE, "owner/repo")["mode"], "full")

    def test_stale_and_unsupported_manifests(self):
        graph = ci.load_graph(validate_sources=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "graph.json"
            for schema in (True, 2):
                path.write_text(json.dumps({**graph, "schema": schema}))
                with self.assertRaises(ValueError): ci.load_graph(path)
            stale = json.loads(json.dumps(graph))
            stale["features"]["apps/ghostty"]["files"].append("modules/apps/ghostty/_deleted.nix")
            path.write_text(json.dumps(stale))
            with self.assertRaisesRegex(ValueError, "Stale"): ci.load_graph(path, validate_sources=True)
            for dependencies in (["missing"], ["apps/ghostty"]):
                stale["features"]["apps/ghostty"]["dependencies"] = dependencies
                path.write_text(json.dumps(stale))
                with self.assertRaises(ValueError): ci.load_graph(path)

    def test_strict_gate_and_tampered_selections(self):
        plans = [self.focused(["README.md"]), self.focused(["modules/apps/ghostty/_package.nix"]), ci.make_plan(None)]
        for plan in plans:
            expected = "skipped" if plan["mode"] == "docs" else "success"
            ci.check_gate(plan, "success", expected)
            for fixtures, nix in (("failure",expected),("cancelled",expected),("skipped",expected),("success","failure")):
                with self.assertRaises(ValueError): ci.check_gate(plan, fixtures, nix)
            if plan["mode"] != "full":
                with self.assertRaises(ValueError): ci.check_gate(plan, "success", expected, full=True)
        original = plans[1]
        for key,value in (("schema3",[]),("checks",[]),("baseline",None),("graph","bad"),("extra",True),("schema",True)):
            with self.assertRaises(ValueError): ci.validate_plan({**original,key:value})

    def test_full_case_set_and_invalid_paths(self):
        import nix_schema3_validation,nix_host_validation,nix_legacy_validation
        for group,mod in (("schema3",nix_schema3_validation),("hosts",nix_host_validation),("legacy",nix_legacy_validation)):
            self.assertEqual(ci.make_plan(None)[group], list(mod.cases()))
        self.assertEqual(len(ci.SCHEMA3)+len(ci.HOSTS)+len(ci.LEGACY),21)
        for paths in (["../x"],["/x"],[None],"x"):
            with self.assertRaises(ValueError): ci.make_plan(paths)

    def test_base_proof_must_match_sha_app_and_success(self):
        valid = {"name": "CI gate", "head_sha": BASE, "status": "completed", "conclusion": "success", "app": {"id": 15368}}
        variants = [valid, {**valid, "name": "Fixtures and workflows"}, {**valid, "head_sha": "b" * 40},
                    {**valid, "status": "in_progress"}, {**valid, "conclusion": "failure"}, {**valid, "app": {"id": 1}}]
        for index, check in enumerate(variants):
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({"check_runs": [check]}).encode()
            with self.subTest(check=check), patch.object(ci.urllib.request, "urlopen", return_value=response):
                self.assertEqual(ci.baseline_green("owner/repo", BASE), index == 0)
        with patch.object(ci.urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertFalse(ci.baseline_green("owner/repo", BASE))
        with patch.object(ci.urllib.request, "urlopen") as request:
            self.assertFalse(ci.baseline_green("../invalid", BASE))
            self.assertFalse(ci.baseline_green("owner/repo", "HEAD"))
            request.assert_not_called()

    def test_rename_from_runtime_to_docs_keeps_the_runtime_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*args):
                return subprocess.check_output(["git", "-c", "user.name=CI fixture", "-c", "user.email=ci@example.invalid",
                                                "-c", "commit.gpgsign=false", *args], cwd=root, text=True, stderr=subprocess.PIPE).strip()
            git("init")
            (root / "runtime.nix").write_text("{}\n")
            git("add", ".")
            git("commit", "-m", "base")
            base = git("rev-parse", "HEAD")
            (root / "runtime.nix").rename(root / "README.md")
            git("add", "-A")
            git("commit", "-m", "rename")
            head = git("rev-parse", "HEAD")
            self.assertEqual(ci.changed_paths(base, head, cwd=root), ["README.md", "runtime.nix"])
            self.assertEqual(ci.make_plan(ci.changed_paths(base, head, cwd=root))["mode"], "full")


if __name__ == "__main__":
    unittest.main()
