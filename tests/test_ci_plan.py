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
    def test_documentation_is_fast(self):
        plan = ci.make_plan(["README.md", "CHANGELOG.md", "docs/releases/RELEASE-0.3.3.md", "docs/releases/0.3.0-publication.json"])
        self.assertEqual(plan["mode"], "docs")
        self.assertFalse(plan["schema3"] or plan["hosts"] or plan["legacy"] or plan["contracts"])

    def test_unknown_shared_and_dependency_changes_are_full(self):
        for path in ("flake.nix", "flake.lock", "VERSION", "foundation.json", "lib/catalog.nix",
                     "modules/aspects/base/shell.nix", "modules/aspects/host.nix", "tests/nix_matrix.py",
                     "scripts/ci_plan.py", ".github/workflows/check.yml", "new-runtime.nix", "docs/code.nix",
                     "modules/aspects/roles/new-role/home.nix", "modules/aspects/roles/developer.nix"):
            with self.subTest(path=path):
                self.assertEqual(ci.make_plan([path])["mode"], "full")

    def test_isolated_role_covers_legacy_and_workstation(self):
        plan = ci.make_plan(["modules/aspects/roles/support/home.nix"])
        self.assertEqual(plan["mode"], "focused")
        self.assertEqual(plan["schema3"], ["all"])
        self.assertEqual(plan["hosts"], ["workstation"])
        self.assertEqual(plan["legacy"], ["schema2-bluefin", "schema2-bluefin-dx"])
        self.assertFalse(plan["contracts"])

    def test_union_of_affected_paths_includes_assets(self):
        plan = ci.make_plan(["README.md", "modules/aspects/capabilities/devops/rootfs/usr/share/finite/zsh/aliases.zsh",
                             "modules/aspects/hardware/dell-xps-9350-intel/dell-ipu7.conf"])
        self.assertEqual(plan["schema3"], ["minimal", "capabilities", "dell-mixed", "all"])
        self.assertEqual(plan["hosts"], ["generic", "dell-camera-disabled", "workstation"])
        self.assertEqual(plan["mode"], "focused")

    def test_shared_change_overrides_focused_and_docs(self):
        self.assertEqual(ci.make_plan(["README.md", "lib/ghostty-package.nix", "lib/default.nix"])["mode"], "full")

    def test_recipe_selection(self):
        self.assertEqual(ci.make_plan(["lib/ghostty-package.nix"])["schema3"], ["capabilities", "dell-mixed", "all"])
        self.assertEqual(ci.make_plan(["lib/without-icon-build-files.nix"])["schema3"], ["all"])

    def test_no_comparison_or_changes_runs_full(self):
        for paths in (None, []):
            self.assertEqual(ci.make_plan(paths)["mode"], "full")
        self.assertEqual(ci.make_plan(["README.md"], full=True)["mode"], "full")

    def test_release_manual_merge_and_unknown_events_force_full(self):
        for event, ref in (("push", "refs/tags/v0.3.4"), ("workflow_dispatch", "refs/heads/main"),
                           ("merge_group", "refs/heads/gh-readonly-queue/main/test"), ("workflow_call", "refs/heads/main"),
                           ("unknown", "refs/heads/main")):
            with self.subTest(event=event):
                self.assertTrue(ci.requires_full(event, ref))
        self.assertFalse(ci.requires_full("pull_request", "refs/pull/1/merge"))
        self.assertFalse(ci.requires_full("push", "refs/heads/main"))
        self.assertTrue(ci.requires_full("push", "refs/heads/main", requested=True))

    def test_gate_accepts_only_expected_success_or_documented_skip(self):
        plans = [ci.make_plan(["README.md"], baseline=BASE), ci.make_plan(["lib/ghostty-package.nix"], baseline=BASE), ci.make_plan(None)]
        for plan in plans:
            for fixtures in ("success", "failure", "skipped", "cancelled", ""):
                for nix in ("success", "failure", "skipped", "cancelled", ""):
                    with self.subTest(mode=plan["mode"], fixtures=fixtures, nix=nix):
                        if fixtures == "success" and nix == ("skipped" if plan["mode"] == "docs" else "success"):
                            ci.check_gate(plan, fixtures, nix)
                        else:
                            with self.assertRaises(ValueError):
                                ci.check_gate(plan, fixtures, nix)

    def test_full_event_cannot_accept_a_short_plan(self):
        for path in ("README.md", "lib/ghostty-package.nix"):
            plan = ci.make_plan([path], baseline=BASE)
            with self.assertRaisesRegex(ValueError, "full validation"):
                ci.check_gate(plan, "success", "skipped" if plan["mode"] == "docs" else "success", full=True)

    def test_omitted_cases_extra_keys_and_reclassified_plans_are_rejected(self):
        original = ci.make_plan(["lib/ghostty-package.nix"], baseline=BASE)
        variants = [None, {}, {**original, "schema": True}, {**original, "contracts": 0},
                    {**original, "schema3": []}, {**original, "legacy": []},
                    {**original, "mode": "docs"}, {**original, "extra": True}, {**original, "baseline": None}]
        full = ci.make_plan(None)
        variants.append({**full, "hosts": full["hosts"][:-1]})
        for plan in variants:
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                ci.validate_plan(plan)

    def test_invalid_paths_and_missing_commits(self):
        for paths in (["../README.md"], ["/README.md"], [None], "README.md"):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                ci.make_plan(paths)
        for base, head in ((None, None), ("0" * 40, "a" * 40), ("HEAD;true", "a" * 40), ("a" * 40, "b" * 40)):
            self.assertIsNone(ci.changed_paths(base, head))

    def test_full_plan_matches_every_real_matrix_case(self):
        import nix_schema3_validation
        import nix_host_validation
        import nix_legacy_validation
        self.assertEqual(ci.SCHEMA3, list(nix_schema3_validation.cases()))
        self.assertEqual(ci.HOSTS, list(nix_host_validation.cases()))
        self.assertEqual(ci.LEGACY, list(nix_legacy_validation.cases()))

    def test_missing_plan_cannot_pass_cli_gate(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/ci_plan.py"), "gate"], text=True, capture_output=True,
                                env={**os.environ, "CI_PLAN": "", "FIXTURES_RESULT": "success", "NIX_RESULT": "skipped"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CI plan error", result.stderr)

    def test_workflow_outputs_flow_into_the_gate_and_manual_run_rejects_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event = root / "event.json"
            event.write_text(json.dumps({"pull_request": {"base": {"sha": BASE}}}))
            environment = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_REF": "refs/pull/1/merge",
                           "GITHUB_SHA": "b" * 40, "GITHUB_REPOSITORY": "owner/repo", "CI_FULL": "false",
                           "GITHUB_EVENT_PATH": str(event), "GITHUB_OUTPUT": str(root / "outputs"),
                           "GITHUB_STEP_SUMMARY": str(root / "summary")}
            with patch.dict(os.environ, environment), patch.object(sys, "argv", ["ci_plan.py", "plan"]), \
                    patch.object(ci, "changed_paths", return_value=["README.md"]) as changed, \
                    patch.object(ci, "baseline_green", return_value=True), contextlib.redirect_stdout(io.StringIO()):
                ci.main()
            changed.assert_called_once_with(BASE, "b" * 40)
            outputs = dict(line.split("=", 1) for line in (root / "outputs").read_text().splitlines())
            self.assertEqual(outputs["mode"], "docs")
            self.assertEqual(json.loads(outputs["plan"])["baseline"], BASE)
            environment.update(CI_PLAN=outputs["plan"], FIXTURES_RESULT="success", NIX_RESULT="skipped")
            with patch.dict(os.environ, environment), patch.object(sys, "argv", ["ci_plan.py", "gate"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                ci.main()
            environment["GITHUB_EVENT_NAME"] = "workflow_dispatch"
            with patch.dict(os.environ, environment), patch.object(sys, "argv", ["ci_plan.py", "gate"]), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as rejected:
                ci.main()
            self.assertEqual(rejected.exception.code, 1)

    def test_short_plans_require_verified_base_success(self):
        for path in ("README.md", "lib/ghostty-package.nix"):
            plan = ci.make_plan([path])
            with patch.object(ci, "baseline_green", return_value=False):
                self.assertEqual(ci.with_baseline(plan, BASE, "owner/repo")["mode"], "full")
            with patch.object(ci, "baseline_green", return_value=True):
                actual = ci.with_baseline(plan, BASE, "owner/repo")
                self.assertEqual(actual["mode"], plan["mode"])
                self.assertEqual(actual["baseline"], BASE)
                ci.validate_plan(actual)
        with patch.object(ci, "baseline_green") as check:
            self.assertEqual(ci.with_baseline(ci.make_plan(None), BASE, "owner/repo")["mode"], "full")
            check.assert_not_called()

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
