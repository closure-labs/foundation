"""Only bounded logger metadata becomes diagnostics; partial coverage is unknown."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import foundation_observations as observations


class Observations(unittest.TestCase):
    def test_parallel_activity_union_and_cross_kind_overlap(self):
        with patch.dict(os.environ, FOUNDATION_TIMINGS='1'), contextlib.redirect_stderr(io.StringIO()) as sink:
            logger = observations.NixActivities(clock=iter([1., 2., 3., 5., 6., 8.]).__next__)
            for action, identity, kind in [('start', 1, 105), ('start', 2, 108), ('start', 3, 105),
                                           ('stop', 1, 105), ('stop', 2, 108), ('stop', 3, 105)]:
                raw = ('@nix ' + json.dumps({'action': action, 'id': identity, 'type': kind,
                                            'text': 'secret path', 'fields': ['private arguments']}) + '\n').encode()
                # Arbitrary chunk boundaries must preserve activity matching.
                logger.feed(raw[:7]); logger.feed(raw[7:])
            logger.finish()
        self.assertNotIn('secret', sink.getvalue())
        self.assertNotIn('private', sink.getvalue())
        row = json.loads(sink.getvalue().removeprefix('FOUNDATION_TIMING '))
        self.assertEqual(row['details']['buildSeconds'], 7.)
        self.assertEqual(row['details']['substitutionSeconds'], 4.)
        self.assertEqual(row['details']['overlapSeconds'], 4.)
        self.assertEqual(row['details']['evaluation'], 'unknown')

    def test_missing_stop_malformed_and_unknown_logger_are_not_zero_cost(self):
        with patch.dict(os.environ, FOUNDATION_TIMINGS='1'), contextlib.redirect_stderr(io.StringIO()) as sink:
            logger = observations.NixActivities()
            logger.feed(b'@nix {"action":"start","id":1,"type":108}\n@nix {bad}\n')
            logger.finish()
        row = json.loads(sink.getvalue().removeprefix('FOUNDATION_TIMING '))['details']
        self.assertTrue(row['incomplete'])
        self.assertIsNone(row['substitutionSeconds'])
        self.assertEqual(row['rejectedRecords'], 1)

    def test_missing_resource_cgroups_remain_unknown(self):
        with patch.dict(os.environ, FOUNDATION_TIMINGS='1'), contextlib.redirect_stderr(io.StringIO()) as sink:
            resources = observations.Resources(root=Path('/nonexistent-fixture'))
            resources.sample(99999999); resources.finish()
        rows = [json.loads(line.removeprefix('FOUNDATION_TIMING ')) for line in sink.getvalue().splitlines()]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertFalse(row['details']['available'])
            self.assertIsNone(row['details']['cpuUsageUsec'])


if __name__ == '__main__': unittest.main()
