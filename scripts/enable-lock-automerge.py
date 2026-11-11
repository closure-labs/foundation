#!/usr/bin/env python3
"""Enable protected auto-merge only for the verified Decider dependency PR."""
import json
import os
import subprocess


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def validate(pr, files, rules, bot, repository):
    if (pr['state'] != 'open' or pr['draft'] or pr['user']['login'] != bot
            or pr['base']['ref'] != 'main'
            or pr['head']['ref'] != 'automation/flake-lock'
            or pr['head']['repo']['full_name'] != repository):
        raise ValueError('Unexpected dependency PR identity or branches')
    if not files or not set(files) <= {'flake.nix', 'flake.lock'}:
        raise ValueError('Dependency PR changes unexpected files')
    reviews = [r['parameters'] for r in rules if r['type'] == 'pull_request']
    checks = [c for r in rules if r['type'] == 'required_status_checks'
              for c in r['parameters']['required_status_checks']]
    if not any(r.get('required_approving_review_count', 0) >= 1
               and r.get('dismiss_stale_reviews_on_push') for r in reviews):
        raise ValueError('main must require approval and dismiss stale reviews in an active ruleset')
    if not any(c['context'] == 'CI gate' and c.get('integration_id') == 15368 for c in checks):
        raise ValueError('main must require the GitHub Actions CI gate in an active ruleset')


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    number = int(os.environ['PR_NUMBER'])
    pr = api(f'repos/{repo}/pulls/{number}')
    files = []
    page = 1
    while True:
        batch = api(f'repos/{repo}/pulls/{number}/files?per_page=100&page={page}')
        files.extend(f['filename'] for f in batch)
        if len(batch) < 100:
            break
        page += 1
    validate(pr, files, api(f'repos/{repo}/rules/branches/main'),
             os.environ['EXPECTED_BOT'], repo)
    subprocess.run(['gh', 'pr', 'merge', str(number), '--repo', repo, '--auto',
                    '--squash', '--match-head-commit', pr['head']['sha']], check=True)


if __name__ == '__main__':
    main()
