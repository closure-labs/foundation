"""Evaluate current host compositions sequentially; no activation or cross-version matrix."""
import json
import subprocess

from test_home import ROOT, home
from test_profile_validation import profile


def main():
    base = {key: value for key, value in profile().items() if key != "hardware"}
    base.update(schema=3, roles=[], packages=[])
    dell = {"formFactor": "laptop", "cpu": "intel", "gpus": ["intel-integrated"], "model": "dell-xps-9350", "camera": True}
    cases = {
        "generic": {},
        "amd-laptop": {"formFactor": "laptop", "cpu": "amd", "gpus": ["amd-integrated"], "camera": True},
        "intel-laptop": {"formFactor": "laptop", "cpu": "intel", "gpus": ["intel-integrated"]},
        "intel-desktop-amd-discrete": {"formFactor": "desktop", "cpu": "intel", "gpus": ["amd-discrete"], "camera": True},
        "amd-desktop-intel-discrete": {"formFactor": "desktop", "cpu": "amd", "gpus": ["intel-discrete"]},
        "amd-integrated-and-discrete": {"formFactor": "desktop", "cpu": "amd", "gpus": ["amd-integrated", "amd-discrete"]},
        "intel-integrated-and-discrete": {"formFactor": "desktop", "cpu": "intel", "gpus": ["intel-integrated", "intel-discrete"]},
        "dell-camera-disabled": {**dell, "camera": False},
        "workstation": None,
    }
    for name, host in cases.items():
        value = {**base, "host": host} if host is not None else json.loads((ROOT / "examples/workstations/dale-xps-9350.json").read_text())
        expression = f'import {ROOT}/tests/host-composition.nix {{ foundation = builtins.getFlake '
        expression += home.nix_value("path:" + str(ROOT)) + '; profile = ' + home.nix_value(value) + '; }'
        result = subprocess.run(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression], text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(f"Host {name}: {result.stderr}")
        actual = json.loads(result.stdout)
        declared = actual["host"]
        laptop = declared["formFactor"] == "laptop"
        is_dell = declared["model"] == "dell-xps-9350"
        assert actual["environment"]["FINITE_FORM_FACTOR"] == declared["formFactor"]
        assert actual["environment"]["FINITE_CPU_VENDOR"] == declared["cpu"]
        assert actual["environment"]["FINITE_HARDWARE"] == ("dell-xps-9350-intel" if is_dell else "generic-x86_64")
        assert actual["environment"]["FINITE_HOST_GPUS"] == ",".join(declared["gpus"])
        markers = {"FINITE_GPU_" + gpu.upper().replace("-", "_") for gpu in declared["gpus"]}
        assert {key for key in actual["environment"] if key.startswith("FINITE_GPU_")} == markers
        assert actual["batteryPercentage"] is (True if laptop else None)
        assert ("finite-dell-xps-9350-panel" in actual["services"]) == is_dell
        assert ("wireplumber/wireplumber.conf.d/50-finite-dell-ipu7.conf" in actual["files"]) == (is_dell and declared["camera"])
        assert not any(any(word in service for word in ("fprint", "tuned", "tlp", "lid-switch")) for service in actual["services"])
        assert not {"DRI_PRIME", "LIBVA_DRIVER_NAME", "LD_LIBRARY_PATH"}.intersection(actual["environment"])
        assert actual["nixgl"] is True and actual["gpu"] is False and actual["vulkan"] is False
        assert actual["firefox"] == actual["expectedFirefox"]
        assert actual["stateVersion"] == "26.05"
        assert actual["catalog"]["gpus"] == ["intel-integrated", "intel-discrete", "amd-integrated", "amd-discrete"]
        if name == "workstation":
            assert declared["fingerprint"] is True and actual["environment"]["FINITE_HOST_FINGERPRINT"] == "1"
        print(f"Host {name}: selected aspects, laptop/model isolation, camera recipe and graphics ownership passed", flush=True)


if __name__ == "__main__":
    main()
