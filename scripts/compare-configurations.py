#!/usr/bin/env python3
"""Compare 21 homes with a baseline checkout without activation or builds."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HELPERS = {"finite-configure", "finite-home-apply", "finite-home-update", "finite-home-migrate", "finite-app-status"}


def normalize(value):
    if isinstance(value, str):
        value = re.sub(r"/nix/store/[a-z0-9]{32}-", "/nix/store/HASH-", value)
        return re.sub(r'/nix/store/HASH-source/[^\s"\n;]+',
                      lambda m: "/nix/store/HASH-source/ASSET/" + m.group().rsplit("/",1)[-1], value)
    if isinstance(value, list): return [normalize(v) for v in value]
    if isinstance(value, dict): return {k: normalize(v) for k,v in value.items()}
    return value


def capture(root, profiles):
    result = {}
    items = list(profiles.items())
    for start in range(0,len(items),2):
        batch = dict(items[start:start+2])
        expr = 'let foundation = builtins.getFlake ' + json.dumps("path:"+str(root)) + '; profiles = builtins.fromJSON ' + json.dumps(json.dumps(batch)) + '; in builtins.mapAttrs (_: profile: import ' + str(ROOT/"tests/configuration-parity.nix") + ' {inherit foundation profile;}) profiles'
        run = subprocess.run(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expr],text=True,capture_output=True,check=True)
        result.update(json.loads(run.stdout))
        print(", ".join(batch),flush=True)
    return result


def compare(before, after):
    assert before.keys() == after.keys()
    for case in before:
        # Check actual package identities, multiplicity, priorities and order.
        old, new = before[case]["packages"], after[case]["packages"]
        assert len(old) == len(new), case
        for a,b in zip(old,new):
            assert a["name"] == b["name"] and a["priority"] == b["priority"], (case,a,b)
            if a["name"] not in HELPERS: assert a["path"] == b["path"], (case,a,b)
        # Remaining generated store references embed relocated source/helper paths.
        assert normalize(before[case]) == normalize(after[case]), case
    return {"cases": list(before), "passed": len(before),
            "packageIdentities": "exact except Foundation helper source bundles",
            "orderedPackagesPrioritiesMultiplicity": "identical",
            "shellFlatpakActivationServicesFiles": "identical after source-reference normalization",
            "expectedChangedPackages": sorted(HELPERS)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    groups=json.loads((ROOT/"modules/ci/profiles/_cases.json").read_text())
    profiles={group+"/"+name:p for group,cases in groups.items() for name,p in cases.items()}
    summary=compare(capture(args.baseline.resolve(),profiles),capture(ROOT,profiles))
    args.output.write_text(json.dumps(summary,indent=2)+"\n")


if __name__ == "__main__": main()
