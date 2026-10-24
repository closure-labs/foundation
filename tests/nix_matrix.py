"""Share pinned inputs within bounded batches, retaining every case assertion."""

import argparse
import json
import subprocess

from test_home import ROOT, home


def selection(cases, selected=None):
    if selected is None:
        return cases
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(cases):
        raise ValueError("Unknown, duplicate or empty Nix case selection")
    return {name: value for name, value in cases.items() if name in selected}


def evaluate(projection, cases, selected=None, batch_size=2):
    if batch_size not in (1, 2):
        raise ValueError("Nix evaluation batch size must be 1 or 2")
    items = list(selection(cases, selected).items())
    for offset in range(0, len(items), batch_size):
        batch = dict(items[offset:offset + batch_size])
        expression = 'let foundation = builtins.getFlake ' + home.nix_value("path:" + str(ROOT)) + '; '
        expression += 'profiles = builtins.fromJSON ' + home.nix_value(json.dumps(batch)) + '; '
        expression += f'in builtins.mapAttrs (_: profile: import {ROOT}/tests/{projection} {{ inherit foundation profile; }}) profiles'
        result = subprocess.run(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression],
                                text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(f"Nix cases {', '.join(batch)}: {result.stderr}")
        actual = json.loads(result.stdout)
        if set(actual) != set(batch):
            raise ValueError("Nix evaluation returned a different case set")
        for name, value in batch.items():
            print(f"Derivation {name}: {actual[name]['drv']}", flush=True)
            yield name, value, actual[name]


def arguments(cases):
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", dest="selected", action="append", choices=list(cases))
    parser.add_argument("--batch-size", type=int, choices=(1, 2), default=2)
    return parser.parse_args()
