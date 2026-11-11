import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('lock_merge', Path(__file__).resolve().parents[1] / 'scripts/enable-lock-automerge.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LockAutoMergeTests(unittest.TestCase):
    def setUp(self):
        self.pr = {'state': 'open', 'draft': False, 'user': {'login': 'ci-decider[bot]'},
                   'base': {'ref': 'main'}, 'head': {'ref': 'automation/flake-lock',
                   'repo': {'full_name': 'closure-labs/foundation'}}}
        self.rules = [
            {'type': 'pull_request', 'parameters': {'required_approving_review_count': 1,
             'dismiss_stale_reviews_on_push': True}},
            {'type': 'required_status_checks', 'parameters': {'required_status_checks': [
             {'context': 'CI gate', 'integration_id': 15368}]}}]

    def validate(self, files=None):
        module.validate(self.pr, files or ['flake.lock'], self.rules,
                        'ci-decider[bot]', 'closure-labs/foundation')

    def test_protected_update(self):
        self.validate(['flake.nix', 'flake.lock', 'modules/flake/framework/default.nix',
                       'modules/ci/_graph.json', 'docs/ARCHITECTURE.md'])

    def test_wrong_author_or_fork(self):
        self.pr['user']['login'] = 'someone'
        with self.assertRaises(ValueError):
            self.validate()
        self.pr['user']['login'] = 'ci-decider[bot]'
        self.pr['head']['repo']['full_name'] = 'someone/foundation'
        with self.assertRaises(ValueError):
            self.validate()

    def test_unexpected_file(self):
        with self.assertRaises(ValueError):
            self.validate(['flake.lock', '.github/workflows/check.yml'])

    def test_missing_protection(self):
        original = copy.deepcopy(self.rules)
        for rules in [[], original[:1], original[1:]]:
            self.rules = rules
            with self.assertRaises(ValueError):
                self.validate()

    def test_stale_approval_and_wrong_check_source(self):
        self.rules[0]['parameters']['dismiss_stale_reviews_on_push'] = False
        with self.assertRaises(ValueError):
            self.validate()
        self.rules[0]['parameters']['dismiss_stale_reviews_on_push'] = True
        self.rules[1]['parameters']['required_status_checks'][0]['integration_id'] = 42
        with self.assertRaises(ValueError):
            self.validate()
