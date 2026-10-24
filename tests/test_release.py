import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("release", Path(__file__).resolve().parents[1] / "scripts/release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "VERSION").write_text("0.1.0\n")
        (self.root / "foundation.json").write_text(json.dumps({"schema": 1, "compatibility": 1, "version": "0.1.0"}))
        self.changelog = """# Changelog

## [Unreleased]

- Future work that must not leak into release notes.

## [0.1.0] - 2026-10-16

### Added

- The first release.

## [0.0.1] - 2026-10-01

- Older work that must not leak into release notes.

[0.1.0]: https://example.com/releases/v0.1.0
"""
        self.write_changelog(self.changelog)

    def write_changelog(self, contents):
        (self.root / "CHANGELOG.md").write_text(contents)

    def test_extracts_only_matching_version(self):
        self.assertEqual(release.release_metadata(self.root, "v0.1.0"), ("0.1.0", "### Added\n\n- The first release.\n"))

    def test_initial_release_omits_trailing_links(self):
        self.write_changelog(self.changelog.split("## [0.0.1]")[0] + "[0.1.0]: https://example.com\n")
        self.assertEqual(release.release_metadata(self.root)[1], "### Added\n\n- The first release.\n")

    def test_rejects_wrong_tags(self):
        for tag in ("v0.2.0", "0.1.0", "v0.1.0-rc.1", "v0.1.0;echo injected"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.release_metadata(self.root, tag)

    def test_rejects_invalid_versions(self):
        for version in ("", "v0.1.0", "0.1", "00.1.0", "0.1.0\n0.2.0"):
            (self.root / "VERSION").write_text(version)
            with self.subTest(version=version), self.assertRaises(ValueError):
                release.release_metadata(self.root)

    def test_rejects_mismatched_foundation_version(self):
        (self.root / "foundation.json").write_text(json.dumps({"schema": 1, "version": "0.0.1"}))
        with self.assertRaisesRegex(ValueError, "version must match VERSION"):
            release.release_metadata(self.root, "v0.1.0")

    def test_rejects_invalid_foundation_metadata(self):
        for metadata in ({"schema": 2, "version": "0.1.0"}, {"schema": 1}, [], None):
            with self.subTest(metadata=metadata):
                (self.root / "foundation.json").write_text(json.dumps(metadata))
                with self.assertRaisesRegex(ValueError, "foundation.json"):
                    release.release_metadata(self.root)

    def test_rejects_missing_foundation_metadata(self):
        (self.root / "foundation.json").unlink()
        with self.assertRaises(FileNotFoundError):
            release.release_metadata(self.root)

    def test_rejects_malformed_foundation_metadata(self):
        (self.root / "foundation.json").write_text("{")
        with self.assertRaises(json.JSONDecodeError):
            release.release_metadata(self.root)

    def test_rejects_missing_duplicate_undated_and_empty_sections(self):
        variants = (
            self.changelog.replace("[0.1.0]", "[0.2.0]"),
            self.changelog + "\n## [0.1.0] - 2026-10-16\n\n- Duplicate.\n",
            self.changelog.replace(" - 2026-10-16", " - Unreleased"),
            self.changelog.replace("2026-10-16", "2026-02-30"),
            self.changelog.replace("- The first release.", ""),
        )
        for contents in variants:
            self.write_changelog(contents)
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                release.release_metadata(self.root)


if __name__ == "__main__":
    unittest.main()
