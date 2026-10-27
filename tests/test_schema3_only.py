"""Schema rejection must happen locally, without Nix or consumer changes."""
import json
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_home import home, ROOT, INFO, LOCK


class SchemaThreeOnly(unittest.TestCase):
    def test_descriptor_advertises_only_schema_three(self):
        capabilities = home.profile_capabilities()
        for field in ("initializeSchemas", "normalizeSchemas", "editSchemas"):
            self.assertEqual(capabilities[field], [3])
        self.assertEqual(capabilities["writeSchema"], 3)

    def test_persisted_unsupported_profiles_never_query_nix_or_change_files(self):
        for schema in (1, 2, 4, True, "3", 3.0):
            with self.subTest(schema=schema), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "home-manager"
                home.make_template(ROOT, INFO, root, LOCK)
                value = {**home.read_json(root / "profile.json"), "schema": schema}
                home.write_json(root / "profile.json", value)
                before = home.tree_digest(root)
                with patch.object(home, "capture") as capture, patch.object(home, "run") as run, patch.object(home, "github_api") as releases, patch.object(home, "available") as available:
                    for action in (home.validate_staged_profile, home.read_editor, home.apply, home.update, lambda root: home.migrate(root, INFO, LOCK)):
                        with self.assertRaisesRegex(ValueError, "recreate.*foundation home profile"):
                            action(root)
                    for operation in (capture, run, releases, available):
                        operation.assert_not_called()
                self.assertEqual(home.tree_digest(root), before)
                self.assertFalse((root.parent / ".foundation.lock").exists())

    def test_migrate_cli_rejects_schema_two_before_release_lookup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "home-manager"
            home.make_template(ROOT, INFO, root, LOCK)
            home.write_json(root / "profile.json", {"schema": 2})
            before = home.tree_digest(root)
            with patch.object(sys, "argv", ["foundation", "migrate"]), patch.object(home.os, "geteuid", return_value=1000), patch.object(home, "config_root", return_value=root), patch.object(home, "github_api") as releases, patch.object(home, "main_data") as release, patch.object(home, "capture") as capture, patch.object(home, "run") as run, contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(home.main(), 2)
                self.assertIn("recreate the selection with foundation home profile", stderr.getvalue())
                for operation in (releases, release, capture, run):
                    operation.assert_not_called()
            self.assertEqual(home.tree_digest(root), before)
            self.assertFalse((root.parent / ".foundation.lock").exists())

    def test_initializer_rejects_schema_two_before_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "new-home"
            with patch.object(home, "capture", return_value=json.dumps({"schema": 2})), patch.object(home, "make_template") as template:
                with self.assertRaisesRegex(ValueError, "recreate.*foundation home profile"):
                    home.initialize(root, Path(temporary) / "profile.yaml")
                template.assert_not_called()
            self.assertFalse(root.exists())

if __name__ == "__main__":
    unittest.main()
