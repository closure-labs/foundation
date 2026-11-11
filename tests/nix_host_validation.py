"""Evaluate current host compositions in bounded batches; never activate."""
import json

from test_home import ROOT
from test_profile_validation import profile
from nix_matrix import arguments, evaluate


def cases():
    import json
    from test_home import ROOT
    return json.loads((ROOT / "modules/ci/profiles/_cases.json").read_text())["hosts"]


def main():
    profiles = cases()
    args = arguments(profiles)
    for name, value, actual in evaluate("host-composition.nix", profiles, args.selected, args.batch_size):
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
        assert (actual["dellGrubActivation"] is not None) == is_dell
        assert actual["dellGrubOptOut"] is False
        if is_dell:
            assert "install --dry-run" in actual["dellGrubActivation"]
        assert "wireplumber/wireplumber.conf.d/50-finite-dell-ipu7.conf" not in actual["files"]
        assert (actual["ipu7Activation"] is not None) == declared["camera"]
        assert actual["ipu7OptOut"] is False
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
