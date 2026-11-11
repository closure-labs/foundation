"""Runtime root precedence does not mistake NH flake references for local paths."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from test_home import home


class ConfigRootTests(unittest.TestCase):
    def resolve(self, **environment):
        with patch.dict(os.environ, environment, clear=True), patch.object(home.Path, "home", return_value=Path("/home/alice")):
            return home.config_root()

    def test_defaults_to_home_config(self):
        self.assertEqual(self.resolve(), Path("/home/alice/.config/home-manager"))

    def test_runtime_xdg_override(self):
        self.assertEqual(self.resolve(XDG_CONFIG_HOME="/custom config"), Path("/custom config/home-manager"))

    def test_explicit_foundation_root_precedes_xdg(self):
        self.assertEqual(self.resolve(FINITE_HOME_FLAKE_PATH="/explicit root", XDG_CONFIG_HOME="/custom"), Path("/explicit root"))

    def test_empty_overrides_fall_back(self):
        self.assertEqual(self.resolve(FINITE_HOME_FLAKE_PATH="", XDG_CONFIG_HOME="/custom"), Path("/custom/home-manager"))
        self.assertEqual(self.resolve(FINITE_HOME_FLAKE_PATH="", XDG_CONFIG_HOME=""), Path("/home/alice/.config/home-manager"))

    def test_nh_references_are_not_writable_foundation_paths(self):
        self.assertEqual(self.resolve(NH_HOME_FLAKE="github:owner/repo#user", NH_FLAKE="path:/other"), Path("/home/alice/.config/home-manager"))

    def test_local_flake_reference_encodes_spaces_and_delimiters(self):
        self.assertEqual(home.path_flake(Path("/custom config/a#b?c%25")),
                         "path:/custom%20config/a%23b%3Fc%2525")
        self.assertEqual(home.path_flake(Path("./consumer")), "path:consumer")

    def test_existing_relative_cli_override_stays_compatible(self):
        self.assertEqual(self.resolve(FINITE_HOME_FLAKE_PATH="./consumer"), Path("consumer"))


if __name__ == "__main__":
    unittest.main()
