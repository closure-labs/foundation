"""Verify stable selection, publication gates, idempotency and branch writes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("channel", Path(__file__).resolve().parents[1] / "scripts/release-channel.py")
channel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(channel)
SHA = "a" * 40
GREEN = {"name": "CI gate", "status": "completed", "conclusion": "success", "app": {"slug": "github-actions"}}


def release(tag, **kwargs):
    return {"tag_name": tag, "draft": False, "prerelease": False, "published_at": "2026-10-16", **kwargs}


class ChannelTests(unittest.TestCase):
    def test_selects_semver_not_publication_order_ignoring_unpublished_and_prereleases(self):
        releases = [release("v0.2.10"), release("v0.2.9"), release("v0.3.0", draft=True),
                    release("v0.4.0", prerelease=True), release("v0.5.0", published_at=None),
                    release("v0.6.0-rc.1"), release("v00.7.0"), release("latest-release")]
        self.assertEqual(channel.latest_stable(releases), "v0.2.10")
        with self.assertRaises(ValueError):
            channel.latest_stable([release("v1.0.0", draft=True)])

    def test_requires_completed_successful_github_ci(self):
        channel.require_green([GREEN])
        for change in ({"conclusion": "failure"}, {"status": "in_progress"}, {"app": {"slug": "other"}}, {"name": "unrelated"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                channel.require_green([{**GREEN, **change}])

    def exercise(self, current=None, check=False, previous="0.2.0", ancestor=True):
        refs = [{"ref": "refs/heads/latest-release", "object": {"sha": current}}] if current else []
        calls = [[release("v0.2.1")]], [{"check_runs": [GREEN]}], refs
        values = [SHA, "0.2.1", json.dumps({"schema": 1, "version": "0.2.1"})]
        if current and current != SHA:
            values.append(previous)
        with patch.object(channel, "api", side_effect=[*calls, {}]) as api, patch.object(channel, "capture", side_effect=values), patch.object(channel.subprocess, "run") as run:
            if not ancestor:
                run.side_effect = [None, subprocess.CalledProcessError(1, "merge-base")]
                with self.assertRaises(subprocess.CalledProcessError):
                    channel.advance(check)
            elif previous == "0.3.0":
                with self.assertRaisesRegex(ValueError, "older or equal"):
                    channel.advance(check)
            else:
                channel.advance(check)
        return api.call_args_list

    def test_creates_branch_at_validated_commit(self):
        self.assertEqual(self.exercise()[-1].args, ("git/refs", {"ref": "refs/heads/latest-release", "sha": SHA}))

    def test_advances_without_force(self):
        self.assertEqual(self.exercise("b" * 40)[-1].args, ("git/refs/heads/latest-release", {"sha": SHA, "force": False}))

    def test_retry_and_preview_do_not_write(self):
        self.assertEqual(len(self.exercise(SHA)), 3)
        self.assertEqual(len(self.exercise(check=True)), 3)

    def test_rollback_and_non_fast_forward_fail_without_writes(self):
        self.assertEqual(len(self.exercise("b" * 40, previous="0.3.0")), 3)
        self.assertEqual(len(self.exercise("b" * 40, ancestor=False)), 3)


if __name__ == "__main__":
    unittest.main()
