"""Case batching may share inputs but must not omit assertions or hide failures."""
import json
import subprocess
import unittest
from unittest.mock import patch

import nix_matrix


class NixMatrixTests(unittest.TestCase):
    def test_case_selection_preserves_canonical_order(self):
        cases = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(nix_matrix.selection(cases, ["c", "a"]), {"a": 1, "c": 3})
        for selected in ([], ["missing"], ["a", "a"]):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                nix_matrix.selection(cases, selected)

    def test_two_case_batches_share_one_foundation_and_yield_every_case(self):
        cases = {"a": {"schema": 3}, "b": {"schema": 3}, "c": {"schema": 3}}
        responses = [subprocess.CompletedProcess([], 0, json.dumps({"a": {"drv": "a.drv"}, "b": {"drv": "b.drv"}})),
                     subprocess.CompletedProcess([], 0, json.dumps({"c": {"drv": "c.drv"}}))]
        with patch.object(nix_matrix.subprocess, "run", side_effect=responses) as run:
            actual = list(nix_matrix.evaluate("projection.nix", cases))
        self.assertEqual([name for name, _, _ in actual], list(cases))
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][-1].count("builtins.getFlake"), 1)

    def test_failed_or_missing_case_fails_the_batch(self):
        for response in (subprocess.CompletedProcess([], 1, "", "evaluation failed"),
                         subprocess.CompletedProcess([], 0, "{}", "")):
            with self.subTest(response=response), patch.object(nix_matrix.subprocess, "run", return_value=response):
                with self.assertRaises((RuntimeError, ValueError)):
                    list(nix_matrix.evaluate("projection.nix", {"a": {}}))

    def test_batch_size_cannot_grow_without_a_memory_review(self):
        for size in (0, 3, 100):
            with self.subTest(size=size), self.assertRaises(ValueError):
                list(nix_matrix.evaluate("projection.nix", {"a": {}}, batch_size=size))


if __name__ == "__main__":
    unittest.main()
