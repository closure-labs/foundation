import importlib.util
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
