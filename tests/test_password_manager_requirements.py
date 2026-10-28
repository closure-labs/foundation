"""Host requirements are validated before preparation, without privilege changes."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("requirements", ROOT / "scripts/password_manager_requirements.py")
requirements = importlib.util.module_from_spec(spec)
spec.loader.exec_module(requirements)


class HostRequirements(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.generation = Path(self.temp.name)
        self.value = {
            "schema": 1, "manager": "1password", "package": "/nix/store/" + "a" * 32 + "-1password",
            "helper": "/nix/store/" + "b" * 32 + "-1password/share/1password/1Password-BrowserSupport",
            "helperSha256": hashlib.sha256(b"helper").hexdigest(),
            "wrapper": "/nix/store/" + "c" * 32 + "-wrapper/bin/1Password-BrowserSupport",
            "wrapperSha256": hashlib.sha256(b"wrapper").hexdigest(),
            "hostPath": "/var/lib/finite/password-managers/1password/" + "c" * 32 + "-wrapper/1Password-BrowserSupport",
        }
        self.overrides = {}
        self.missing = set()
        self.alias = Path(self.value['package']) / 'share'
        self.alias_target = Path(self.value['helper']).parents[1]
        self.contents = {self.value['helper']: b'helper', self.value['wrapper']: b'wrapper', self.value['hostPath']: b'wrapper'}

    def write(self):
        (self.generation / "foundation-password-managers.json").write_text(json.dumps(self.value))

    @contextlib.contextmanager
    def installed(self, gid=1001):
        original_read = Path.read_bytes
        original_link = Path.readlink
        def contents(path):
            return self.contents[str(path)] if str(path) in self.contents else original_read(path)
        def info(path):
            name = str(path)
            if name in self.missing:
                raise FileNotFoundError(name)
            if path == self.alias:
                mode = stat.S_IFLNK | 0o777
            elif name in (self.value['helper'], self.value['wrapper']):
                mode = stat.S_IFREG | 0o555
            elif name == self.value['hostPath']:
                mode = stat.S_IFREG | 0o2755
            else:
                mode = stat.S_IFDIR | 0o755
            values = {'st_mode': mode, 'st_uid': 0, 'st_gid': gid}
            values.update(self.overrides.get(name, {}))
            return SimpleNamespace(**values)
        def link(path):
            return self.alias_target if path == self.alias else original_link(path)
        with patch.object(requirements.grp, 'getgrnam', return_value=Mock(gr_gid=gid)), \
             patch.object(Path, 'lstat', info), patch.object(Path, 'read_bytes', contents), \
             patch.object(Path, 'readlink', link):
            yield

    def test_absent_manager_has_no_host_requirement(self):
        requirements.check_host_requirements(self.generation)

    def test_invalid_requirement_is_rejected(self):
        for key, value in [("schema", True), ("manager", "other"), ("package", "/tmp/package"),
                           ("helperSha256", "wrong"), ("wrapper", "/bin/sh"),
                           ("hostPath", "/tmp/1Password-BrowserSupport")]:
            with self.subTest(key=key):
                original = self.value[key]
                self.value[key] = value
                self.write()
                with self.assertRaises(ValueError):
                    requirements.check_host_requirements(self.generation)
                self.value[key] = original

    def test_missing_host_helper_reports_exact_review_command_without_running_it(self):
        self.write()
        with patch.object(requirements.grp, "getgrnam", side_effect=KeyError("onepassword")):
            with self.assertRaisesRegex(ValueError, "--approve-wrapper-sha256") as error:
                requirements.check_host_requirements(self.generation)
        self.assertIn(self.value["helperSha256"], str(error.exception))
        self.assertIn(str(self.generation), str(error.exception))

    def test_only_matching_root_owned_setgid_helper_satisfies_requirement(self):
        self.write()
        with self.installed():
            requirements.check_host_requirements(self.generation)
            self.contents[self.value['hostPath']] = b'changed'
            with self.assertRaisesRegex(ValueError, "content differs"):
                requirements.check_host_requirements(self.generation)

    def test_identity_group_requires_gid_larger_than_1000(self):
        self.write()
        for gid in (0, 946, 1000):
            with self.subTest(gid=gid), self.installed(gid=gid), \
                 self.assertRaisesRegex(ValueError, 'GID must be larger than 1000'):
                requirements.check_host_requirements(self.generation)
        with self.installed(gid=1001):
            requirements.check_host_requirements(self.generation)

    def test_missing_source_closure_is_rejected(self):
        self.write()
        for name in ('package', 'helper', 'wrapper'):
            with self.subTest(name=name), self.installed():
                self.missing.add(self.value[name])
                with self.assertRaises(ValueError):
                    requirements.check_host_requirements(self.generation)
                self.missing.clear()

    def test_source_hashes_must_match(self):
        self.write()
        for name in ('helper', 'wrapper'):
            with self.subTest(name=name), self.installed():
                original = self.contents[self.value[name]]
                self.contents[self.value[name]] = b'changed'
                with self.assertRaisesRegex(ValueError, 'source content differs'):
                    requirements.check_host_requirements(self.generation)
                self.contents[self.value[name]] = original

    def test_source_and_destination_ancestors_are_not_writable_symlinks_or_user_owned(self):
        self.write()
        for parent in (Path(self.value['hostPath']).parent, Path(self.value['helper']).parent,
                       Path(self.value['wrapper']).parent):
            for change in ({'st_uid': 1000}, {'st_mode': stat.S_IFDIR | 0o775},
                           {'st_mode': stat.S_IFDIR | 0o757}, {'st_mode': stat.S_IFLNK | 0o777}):
                with self.subTest(parent=str(parent), change=change), self.installed():
                    self.overrides[str(parent)] = change
                    with self.assertRaises(ValueError):
                        requirements.check_host_requirements(self.generation)
                    self.overrides.clear()

    def test_standard_sticky_store_is_allowed_but_not_writable_outputs(self):
        self.write()
        with self.installed():
            self.overrides['/nix/store'] = {'st_mode': stat.S_IFDIR | 0o1775}
            requirements.check_host_requirements(self.generation)
            self.overrides['/nix/store'] = {'st_mode': stat.S_IFDIR | 0o775}
            with self.assertRaises(ValueError):
                requirements.check_host_requirements(self.generation)
            self.overrides['/nix/store'] = {'st_mode': stat.S_IFDIR | 0o1775}
            self.overrides[self.value['package']] = {'st_mode': stat.S_IFDIR | 0o1775}
            with self.assertRaises(ValueError):
                requirements.check_host_requirements(self.generation)

    def test_destination_owner_group_mode_and_type(self):
        self.write()
        for change in ({'st_uid': 1000}, {'st_gid': 201}, {'st_mode': stat.S_IFREG | 0o755},
                       {'st_mode': stat.S_IFREG | 0o6755}, {'st_mode': stat.S_IFREG | 0o2775},
                       {'st_mode': stat.S_IFLNK | 0o777}):
            with self.subTest(change=change), self.installed():
                self.overrides[self.value['hostPath']] = change
                with self.assertRaises(ValueError):
                    requirements.check_host_requirements(self.generation)
                self.overrides.clear()

    def test_package_alias_cannot_escape_store_or_change_helper(self):
        self.write()
        for target in (Path('/tmp/redirect'), Path('/nix/store/' + 'd' * 32 + '-other/share')):
            with self.subTest(target=str(target)), self.installed():
                self.alias_target = target
                with self.assertRaises(ValueError):
                    requirements.check_host_requirements(self.generation)

    def test_approval_command_resolves_generation_symlink_to_real_requirement(self):
        target = self.generation / 'immutable-requirement.json'
        target.write_text(json.dumps(self.value))
        (self.generation / 'foundation-password-managers.json').symlink_to(target)
        command = requirements.approval_command(self.generation, self.value)
        self.assertIn(str(target), command)
        self.assertNotIn(str(self.generation / 'foundation-password-managers.json'), command)

    def test_duplicate_fields_and_non_regular_or_oversized_requirement_are_rejected(self):
        path = self.generation / 'foundation-password-managers.json'
        path.write_text('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            requirements.check_host_requirements(self.generation)
        path.write_text(' ' * 16385)
        with self.assertRaisesRegex(ValueError, 'oversized'):
            requirements.check_host_requirements(self.generation)
        path.unlink(); path.mkdir()
        with self.assertRaisesRegex(ValueError, 'regular JSON file'):
            requirements.check_host_requirements(self.generation)

    def test_failed_preflight_never_runs_generation_preparation(self):
        self.write()
        entry = self.generation / 'foundation-prepare'
        entry.write_text('#!/bin/sh\nexit 0\n'); entry.chmod(0o755)
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            spec = importlib.util.spec_from_file_location('home_requirements_test', ROOT / 'scripts/home.py')
            home = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(home)
            with patch.object(home, 'check_host_requirements', requirements.check_host_requirements), \
                 patch.object(home, 'run') as run, patch.object(home, 'commit_stage') as commit, \
                 self.installed(gid=0):
                with self.assertRaises(ValueError):
                    home.prepare_generation(self.generation)
                run.assert_not_called()
                commit.assert_not_called()
        finally:
            sys.path.pop(0)


if __name__ == '__main__':
    unittest.main()
