"""Verify administrator-installed password-manager helpers before activation.

This module never elevates or writes host state. A generation describes the exact
native wrapper it needs; only a root-owned installation can satisfy that request.
"""
import grp
import hashlib
import json
import os
import re
import shlex
import stat
from pathlib import Path


STORE = re.compile(r"/nix/store/[a-z0-9]{32}-[A-Za-z0-9+._?=-]+")
HEX = re.compile(r"[a-f0-9]{64}")
HOST_ROOT = Path("/var/lib/finite/password-managers/1password")


def read_requirement(activation):
    path = Path(activation) / "foundation-password-managers.json"
    if not path.exists() and not path.is_symlink():
        return None
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Password-manager host requirement must be a regular JSON file")
    if info.st_size > 16384:
        raise ValueError("Password-manager host requirement is oversized")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate password-manager requirement field")
            result[key] = value
        return result
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    keys = {"schema", "manager", "package", "helper", "helperSha256", "wrapper",
            "wrapperSha256", "hostPath"}
    if not isinstance(value, dict) or set(value) != keys or type(value["schema"]) is not int or value["schema"] != 1 or value["manager"] != "1password":
        raise ValueError("Unsupported password-manager host requirement")
    if any(not isinstance(value[key], str) for key in keys - {"schema"}):
        raise ValueError("Invalid password-manager host requirement")
    if not STORE.fullmatch(value["package"]):
        raise ValueError("Password-manager package must be an immutable store output")
    for key, suffix in (("helper", "/share/1password/1Password-BrowserSupport"),
                        ("wrapper", "/bin/1Password-BrowserSupport")):
        if not value[key].endswith(suffix) or not STORE.fullmatch(value[key][:-len(suffix)]):
            raise ValueError("Invalid password-manager helper or wrapper path")
    if not all(HEX.fullmatch(value[key]) for key in ("helperSha256", "wrapperSha256")):
        raise ValueError("Invalid password-manager content hash")
    wrapper_output = Path(value["wrapper"]).parents[1].name
    if value["hostPath"] != str(HOST_ROOT / wrapper_output / "1Password-BrowserSupport"):
        raise ValueError("Invalid password-manager host destination")
    return value


def approval_command(activation, value):
    args = ["sudo", "/usr/libexec/finite/password-manager-setup", "install",
            "--requirement", str((Path(activation) / "foundation-password-managers.json").resolve(strict=True)),
            "--approve-package", value["package"],
            "--approve-helper-sha256", value["helperSha256"],
            "--approve-wrapper-sha256", value["wrapperSha256"]]
    return shlex.join(args)


def _trusted(path, *, directory=False):
    info = path.lstat()
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    # Standard Nix stores are root-owned, sticky and build-group-writable.
    # Sticky ownership protects root-owned entries; every object below the
    # store still requires non-writable directories and administrator ownership.
    sticky_store = directory and path == Path("/nix/store") and info.st_mode & stat.S_ISVTX
    if not expected(info.st_mode) or info.st_uid != 0 or (info.st_mode & 0o022 and not sticky_store):
        raise ValueError("Password-manager artifact has unsafe ownership, type, or permissions")
    return info


def _parents(path):
    for parent in path.parents:
        _trusted(parent, directory=True)


def _package_helper(package):
    """Resolve only root-owned package aliases confined to the immutable store."""
    store = Path("/nix/store")
    path = package / "share/1password/1Password-BrowserSupport"
    for _ in range(40):
        try:
            parts = path.relative_to(store).parts
        except ValueError as error:
            raise ValueError("Password-manager package alias escapes the Nix store") from error
        _parents(store)
        _trusted(store, directory=True)
        current = store
        for index, part in enumerate(parts):
            current /= part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                if info.st_uid != 0:
                    raise ValueError("Password-manager package alias is not root-owned")
                target = current.readlink()
                if not target.is_absolute():
                    target = current.parent / target
                path = Path(os.path.normpath(str(target.joinpath(*parts[index + 1:]))))
                break
            _trusted(current, directory=index < len(parts) - 1)
        else:
            return current
    raise ValueError("Too many password-manager package aliases")


def _check_sources(value):
    package = Path(value["package"])
    _parents(package)
    _trusted(package, directory=True)
    helper = Path(value["helper"])
    if _package_helper(package) != helper:
        raise ValueError("Selected password-manager package and helper do not match")
    for name in ("helper", "wrapper"):
        source = Path(value[name])
        _parents(source)
        info = _trusted(source)
        if not info.st_mode & 0o111:
            raise ValueError("Password-manager source is not executable")
        if hashlib.sha256(source.read_bytes()).hexdigest() != value[name + "Sha256"]:
            raise ValueError("Password-manager source content differs from this generation")


def check_host_requirements(activation):
    value = read_requirement(activation)
    if value is None:
        return
    destination = Path(value["hostPath"])
    reason = None
    try:
        group = grp.getgrnam("onepassword").gr_gid
        if group <= 0:
            raise ValueError("The onepassword identity group must not be root")
        _check_sources(value)
        # Every containing directory is privileged state, never a user-owned link.
        _parents(destination)
        info = _trusted(destination)
        if info.st_gid != group or stat.S_IMODE(info.st_mode) != 0o2755:
            raise ValueError("Host helper ownership or permissions differ from the approved requirement")
        if hashlib.sha256(destination.read_bytes()).hexdigest() != value["wrapperSha256"]:
            raise ValueError("Host helper content differs from this generation")
    except (OSError, KeyError, ValueError) as error:
        reason = str(error)
    if reason is not None:
        raise ValueError(
            "1Password needs its administrator-installed browser helper before activation. "
            + reason + ". Review the exact package and hashes, then run: "
            + approval_command(activation, value)
        )
