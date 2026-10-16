#!/usr/bin/env python3
"""Install, migrate and update a personal consumer of published Foundation releases."""
import argparse
import contextlib
import copy
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPOSITORY = "closure-labs/foundation"
COMPATIBILITY = 1
CORE = {"den", "gen", "devenv", "nixpkgs", "nixpkgs-weekly", "home-manager", "determinate", "nix-flatpak"}
EXCLUDED = {".git", ".jj", ".agents", ".aws", ".codex", ".direnv", ".devenv", "result"}
REFERENCE = re.compile(r'^(\s*foundation\.url = ")github:closure-labs/foundation/([a-f0-9]{40}|v[0-9]+\.[0-9]+\.[0-9]+)(";)$', re.MULTILINE)


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, **kwargs)


def capture(command):
    return run(command, stdout=subprocess.PIPE).stdout.strip()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def config_root():
    return Path(os.environ.get("FINITE_HOME_FLAKE_PATH", str(Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "home-manager")))


def source_root():
    return Path(os.environ.get("FINITE_FOUNDATION_SOURCE", Path(__file__).resolve().parents[1]))


def version(value):
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value):
        raise ValueError(f"Invalid release version: {value}")
    return tuple(map(int, value.split(".")))


def validate_metadata(info):
    if info.get("schema") != 1 or info.get("compatibility") != COMPATIBILITY:
        raise ValueError("Unsupported Foundation consumer compatibility version")
    version(info["version"])
    if not re.fullmatch(r"[a-f0-9]{40}", info.get("rev") or ""):
        raise ValueError("Foundation must be pinned to an immutable Git commit")
    if not re.fullmatch(r"sha256-[A-Za-z0-9+/]{43}=", info.get("narHash") or ""):
        raise ValueError("Foundation source content hash is missing or invalid")


def consumer_lock(lock, info):
    """Re-root a release's committed graph; follows paths belong to its old root."""
    validate_metadata(info)
    old_root = lock["root"]
    names = {name: "foundation" if name == old_root else "foundation-" + name for name in lock["nodes"]}
    def reference(ref):
        return ["foundation", *ref] if isinstance(ref, list) else names[ref]
    nodes = {}
    for name, node in lock["nodes"].items():
        node = copy.deepcopy(node)
        if "inputs" in node:
            node["inputs"] = {key: reference(ref) for key, ref in node["inputs"].items()}
        nodes[names[name]] = node
    nodes["foundation"].update({
        "locked": {"type": "github", "owner": "closure-labs", "repo": "foundation",
                   **{key: info[key] for key in ("rev", "narHash", "lastModified") if key in info}},
        "original": {"type": "github", "owner": "closure-labs", "repo": "foundation", "rev": info["rev"]},
    })
    nodes["root"] = {"inputs": {"foundation": "foundation"}}
    return {"version": 7, "root": "root", "nodes": nodes}


def locked_graph(lock, reference, ancestors=()):
    if isinstance(reference, list):
        return {"follows": reference}
    if reference in ancestors:
        return {"cycle": ancestors.index(reference)}
    node = lock["nodes"][reference]
    return {"locked": node.get("locked"), "flake": node.get("flake", True),
            "inputs": {name: locked_graph(lock, child, (*ancestors, reference))
                       for name, child in sorted(node.get("inputs", {}).items())}}


def verify_update_lock(old, new, release_lock, info):
    old_inputs = old["nodes"][old["root"]]["inputs"]
    new_inputs = new["nodes"][new["root"]]["inputs"]
    expected = consumer_lock(release_lock, info)
    if set(old_inputs) != set(new_inputs):
        raise ValueError("An update added or removed a personal input")
    if locked_graph(new, new_inputs["foundation"]) != locked_graph(expected, "foundation"):
        raise ValueError("Foundation dependency pins differ from its published release lock")
    for name in old_inputs.keys() - {"foundation"}:
        if locked_graph(old, old_inputs[name]) != locked_graph(new, new_inputs[name]):
            raise ValueError(f"An update changed the personal input {name}")


def nix_value(value):
    if isinstance(value, dict):
        return "{ " + " ".join(json.dumps(k) + " = " + nix_value(v) + ";" for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[ " + " ".join(nix_value(v) for v in value) + " ]"
    if isinstance(value, str):
        return json.dumps(value).replace("${", r"\${")
    return json.dumps(value)


def migrate_input_declarations(inputs):
    """Keep custom input pins while moving their core follows to Foundation."""
    extras = {name: copy.deepcopy(value) for name, value in inputs.items() if name not in CORE}
    if "foundation" in extras:
        raise ValueError("A pre-existing personal input named foundation requires manual migration")
    def rebase(value):
        if not isinstance(value, dict):
            return
        follows = value.get("follows")
        if isinstance(follows, str) and follows.split("/")[0] in CORE:
            value["follows"] = "foundation/" + follows
        for child in value.values():
            rebase(child)
    for value in extras.values():
        rebase(value)
    return extras


def consumer_flake(info, extras=None):
    extra_text = "\n".join("    " + json.dumps(k) + " = " + nix_value(v) + ";" for k, v in (extras or {}).items())
    return '''{
  # Foundation owns the shared modules; this flake and your personal modules are yours.
  inputs = {
    foundation.url = "github:closure-labs/foundation/REVISION";
EXTRAS
  };
  outputs = inputs: let
    profile = builtins.fromJSON (builtins.readFile ./profile.json);
  in {
    homeConfigurations.${profile.identity.username} = inputs.foundation.lib.mkHomeConfiguration {
      inherit profile;
      modules = [./customize.nix ./modules/local.nix];
      extraInputs = builtins.removeAttrs inputs ["self" "foundation"];
    };
  };
}
'''.replace("REVISION", info["rev"]).replace("EXTRAS", extra_text)


def make_template(source, info, output, lock=None, extras=None):
    validate_metadata(info)
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    (output / "modules").mkdir(mode=0o700, exist_ok=True)
    (output / "flake.nix").write_text(consumer_flake(info, extras))
    write_json(output / "flake.lock", consumer_lock(lock or read_json(source / "flake.lock"), info))
    write_json(output / "foundation.json", info)
    # Keep this compatibility marker for callers that identify generated configurations.
    write_json(output / "finite-template.json", {"schema": 1, "generator": "finite-home-init", "version": info["version"]})
    for relative in ("profile.json", "customize.nix", "modules/local.nix"):
        if not (output / relative).exists():
            shutil.copy2(source / relative, output / relative)


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0] in EXCLUDED or relative.parts[0].startswith("result-"):
            continue
        if path.is_symlink():
            digest.update(str(relative).encode() + b"\0link\0" + os.readlink(path).encode())
        elif path.is_file():
            digest.update(str(relative).encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


@contextlib.contextmanager
def locked(root):
    root.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (root.parent / ".foundation.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another Foundation configuration operation is running") from error
        yield


def copy_configuration(source, target):
    shutil.copytree(source, target, symlinks=True, ignore=lambda _p, entries: [
        name for name in entries if name in EXCLUDED or name.startswith("result-")
    ])


def validate_profile(profile, catalog):
    if profile.get("schema") != 2:
        raise ValueError("Unsupported profile schema; migrate a schema-1 profile with the existing initializer first")
    for field, choices in (("roles", catalog["roles"]), ("packages", catalog["packages"])):
        requested = profile.get(field)
        if not isinstance(requested, list) or len(set(requested)) != len(requested) or any(x not in choices for x in requested):
            raise ValueError(f"Invalid or duplicate {field}")
        profile[field] = sorted(requested, key=lambda x: choices[x]["order"])
    if profile.get("foundation") not in catalog["foundations"] or profile.get("hardware") not in catalog["hardware"]:
        raise ValueError("Unsupported host foundation or hardware")
    identity = profile.get("identity", {})
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*[$]?", identity.get("username", "")) or not identity.get("homeDirectory", "").startswith("/"):
        raise ValueError("Invalid account identity")
    import pwd
    if identity["username"] != pwd.getpwuid(os.getuid()).pw_name or Path(identity["homeDirectory"]).resolve() != Path.home().resolve():
        raise ValueError("Profile identity must match the invoking desktop user")
    running = Path(os.environ.get("FINITE_RUNNING_PROFILE_PATH", "/usr/share/finite/profile.json"))
    if running.exists():
        host = read_json(running)
        if profile["foundation"] != host["foundation"] or host["hardware"] not in catalog["hardware"][profile["hardware"]]["imageHardware"]:
            raise ValueError("Profile is incompatible with the running Finite image")


def catalog_data():
    path = os.environ.get("FINITE_FOUNDATION_CATALOG")
    if path:
        return read_json(path)
    raw = json.loads(capture(["nix", "eval", "--json", "--file", str(source_root() / "lib/catalog.nix")]))
    return {name: {item["name"]: item for item in raw[name]} for name in ("roles", "packages", "hardware", "foundations")}


def build(stage):
    profile = read_json(stage / "profile.json")
    validate_profile(profile, catalog_data())
    installable = f"path:{stage}#homeConfigurations.{profile['identity']['username']}.activationPackage"
    command = ["systemd-run", "--user", "--scope", "--quiet", "-p", "MemoryMax=3G", "-p", "MemorySwapMax=512M", "-p", "CPUQuota=100%",
               "nix", "build", "--max-jobs", "1", "--cores", "1", "--no-update-lock-file", "--no-link", "--print-out-paths", installable]
    paths = capture(command).splitlines()
    if len(paths) != 1 or not Path(paths[0], "activate").is_file():
        raise ValueError("Nix did not return one valid Home Manager activation package")
    return Path(paths[0])


def previous_generation():
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    profile = state / "nix/profiles/home-manager"
    return profile.resolve() if profile.exists() else None


def provision_brew(stage):
    # Use the policy and installer from the selected Foundation release.
    expression = 'let root = builtins.getFlake ' + json.dumps("path:" + str(stage)) + '''; f = root.inputs.foundation or root; in {
      bootstrap = builtins.readFile (f.outPath + "/modules/finite-brew-bootstrap");
      status = builtins.readFile (f.outPath + "/modules/finite-brew-migration-status");
      policy = builtins.readFile (f.outPath + "/modules/aspects/base/brew-packages.json");
    }'''
    # nix eval --impure only permits the staged local flake reference; its lock is immutable.
    data = json.loads(capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
    with tempfile.TemporaryDirectory(prefix=".foundation-brew-", dir=stage.parent) as temp:
        policy = Path(temp) / "policy.json"
        bootstrap = Path(temp) / "finite-brew-bootstrap"
        policy.write_text(data["policy"])
        bootstrap.write_text(data["bootstrap"])
        (Path(temp) / "finite-brew-migration-status").write_text(data["status"])
        env = dict(os.environ, FINITE_BREW_POLICY=str(policy))
        run(["bash", str(bootstrap)], env=env)


def commit_stage(root, stage, original, activation, replace_tree=False):
    if (tree_digest(root) if root.exists() else None) != original:
        raise ValueError("Configuration changed during the build; nothing installed")
    previous = previous_generation()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = root.with_name(root.name + ".previous." + stamp)
    consumer = root.exists() and not replace_tree
    committed_files = ("flake.nix", "flake.lock", "foundation.json", "finite-template.json", "profile.json")
    if consumer:
        # Keep personal Git metadata and the configuration directory in place.
        copy_configuration(root, backup)
    else:
        if root.exists():
            root.rename(backup)
        stage.rename(root)
    try:
        if consumer:
            for relative in committed_files:
                temporary = root / ("." + relative + ".foundation-new")
                shutil.copy2(stage / relative, temporary)
                temporary.replace(root / relative)
        run([str(activation / "activate")])
    except BaseException:
        failed = root.with_name(root.name + ".failed." + stamp)
        if consumer:
            copy_configuration(root, failed)
            for relative in committed_files:
                if (backup / relative).exists():
                    shutil.copy2(backup / relative, root / relative)
                else:
                    (root / relative).unlink(missing_ok=True)
        else:
            root.rename(failed)
            if backup.exists():
                backup.rename(root)
        if previous is not None:
            try:
                run([str(previous / "activate")])
            except (OSError, subprocess.CalledProcessError) as error:
                print(f"Previous-generation activation also failed: {error}", file=sys.stderr)
        raise
    finite = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "finite"
    finite.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copy2(root / "profile.json", finite / "profile.json")
    print(f"Foundation activated. Previous configuration: {backup if backup.exists() else 'none (first installation)'}")


def published_releases():
    releases = []
    for page in range(1, 11):
        request = urllib.request.Request(f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}", headers={"Accept": "application/vnd.github+json", "User-Agent": "Foundation-home-update"})
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        for release in batch:
            tag = release.get("tag_name", "")
            if release.get("draft") or release.get("prerelease") or not release.get("published_at") or not tag.startswith("v"):
                continue
            try:
                parsed = version(tag[1:])
            except ValueError:
                continue
            releases.append((parsed, tag))
        if len(batch) < 100:
            break
    return sorted(releases)


def release_data(tag):
    ref = f"github:{REPOSITORY}/{tag}"
    expression = '''let f = builtins.getFlake REF; in {
      metadata = builtins.fromJSON (builtins.readFile (f.outPath + "/foundation.json"));
      lock = builtins.fromJSON (builtins.readFile (f.outPath + "/flake.lock"));
      rev = f.rev; narHash = f.narHash; lastModified = f.lastModified;
    }'''.replace("REF", json.dumps(ref))
    # Resolve a release tag once, then read and build only its immutable commit.
    resolved = json.loads(capture(["nix", "flake", "metadata", "--json", ref]))
    rev = resolved["locked"]["rev"]
    expression = expression.replace(json.dumps(ref), json.dumps(f"github:{REPOSITORY}/{rev}"))
    data = json.loads(capture(["nix", "eval", "--json", "--expr", expression]))
    info = {**data["metadata"], **{key: data[key] for key in ("rev", "narHash", "lastModified")}}
    validate_metadata(info)
    if info["version"] != tag.removeprefix("v"):
        raise ValueError("Published tag does not match Foundation release metadata")
    return info, data["lock"]


def installed_info(root):
    if (root / "foundation.json").exists():
        installed = read_json(root / "foundation.json")
    else:
        # A consumer created by nix flake new gains its exact provenance from its lock.
        lock = read_json(root / "flake.lock")
        reference = lock["nodes"][lock["root"]]["inputs"]["foundation"]
        source = lock["nodes"][reference]["locked"]
        if source.get("owner") != "closure-labs" or source.get("repo") != "foundation":
            raise ValueError("Personal Foundation input points to another repository")
        expression = 'let f = builtins.getFlake ' + json.dumps(f"github:{REPOSITORY}/{source['rev']}") + '; in builtins.fromJSON (builtins.readFile (f.outPath + "/foundation.json"))'
        installed = {**json.loads(capture(["nix", "eval", "--json", "--expr", expression])),
                     **{key: source[key] for key in ("rev", "narHash", "lastModified") if key in source}}
    validate_metadata(installed)
    return installed


def available(root):
    installed = installed_info(root)
    releases = published_releases()
    candidates = [tag for number, tag in releases if number > version(installed["version"])]
    if not candidates:
        return installed, None, None
    info, lock = release_data(candidates[-1])
    return installed, info, lock


def update(root, check=False):
    with locked(root):
        installed, info, lock = available(root)
        if info is None:
            print(f"Foundation {installed['version']} is current")
            return
        print(f"Foundation {installed['version']} -> {info['version']}")
        if check:
            return
        original = tree_digest(root)
        with tempfile.TemporaryDirectory(prefix=".foundation-update-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            copy_configuration(root, stage)
            text = (stage / "flake.nix").read_text()
            matches = list(REFERENCE.finditer(text))
            if len(matches) != 1 or matches[0][2] not in (installed["rev"], "v" + installed["version"]):
                raise ValueError("The Foundation input was customized; update it manually")
            text = REFERENCE.sub(lambda m: m[1] + f"github:{REPOSITORY}/{info['rev']}" + m[3], text)
            (stage / "flake.nix").write_text(text)
            # Nix updates this input closure only, retaining personal input pins.
            run(["nix", "flake", "lock", "path:" + str(stage)])
            new_lock = read_json(stage / "flake.lock")
            verify_update_lock(read_json(root / "flake.lock"), new_lock, lock, info)
            selected = new_lock["nodes"][new_lock["nodes"][new_lock["root"]]["inputs"]["foundation"]]["locked"]
            if selected["rev"] != info["rev"] or selected["narHash"] != info["narHash"]:
                raise ValueError("Resolved Foundation source differs from the reviewed release")
            write_json(stage / "foundation.json", info)
            write_json(stage / "finite-template.json", {"schema": 1, "generator": "finite-home-init", "version": info["version"]})
            activation = build(stage)
            provision_brew(stage)
            commit_stage(root, stage, original, activation)


def migrate(root, info, lock, check=False):
    with locked(root):
        if root.is_symlink() or (root / ".git").exists() or (root / ".jj").exists():
            raise ValueError("Migrate a personal configuration directory, not a Git checkout or symlink; keep the checkout for manual review")
        if (root / "foundation.json").exists():
            raise ValueError("Already a Foundation consumer; use finite-home-update")
        manifest = read_json(source_root() / "legacy-managed.json")
        for relative, hashes in manifest["files"].items():
            path = root / relative
            if path.exists() and (path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() not in hashes):
                raise ValueError(f"Locally modified upstream file requires review: {relative}")
        flake = (root / "flake.nix").read_text()
        normalized = re.sub(r"\s+", "", flake[flake.index("  outputs ="):])
        if hashlib.sha256(normalized.encode()).hexdigest() not in manifest["outputs"]:
            raise ValueError("Custom flake outputs require manual migration")
        inputs = json.loads(capture(["nix", "eval", "--json", "--file", str(root / "flake.nix"), "--apply", "flake: flake.inputs"]))
        extras = migrate_input_declarations(inputs)
        original = tree_digest(root)
        with tempfile.TemporaryDirectory(prefix=".foundation-migrate-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            copy_configuration(root, stage)
            for relative in manifest["files"]:
                (stage / relative).unlink(missing_ok=True)
            make_template(source_root(), info, stage, lock, extras)
            if extras:
                # Seed original custom nodes so lock completion retains their exact pins.
                old_lock = read_json(root / "flake.lock")
                new_lock = read_json(stage / "flake.lock")
                for name, node in old_lock["nodes"].items():
                    if name != old_lock["root"]:
                        if name in new_lock["nodes"]:
                            raise ValueError("Custom input lock-node collision requires manual migration")
                        node = dict(node)
                        if "inputs" in node:
                            node["inputs"] = {key: ["foundation", *ref] if isinstance(ref, list) and ref and ref[0] in CORE else ref
                                              for key, ref in node["inputs"].items()}
                        new_lock["nodes"][name] = node
                old_inputs = old_lock["nodes"][old_lock["root"]]["inputs"]
                new_lock["nodes"]["root"]["inputs"].update({
                    name: ["foundation", *old_inputs[name]] if isinstance(old_inputs[name], list) and old_inputs[name] and old_inputs[name][0] in CORE else old_inputs[name]
                    for name in extras})
                write_json(stage / "flake.lock", new_lock)
                run(["nix", "flake", "lock", "path:" + str(stage)])
            activation = build(stage)
            if not check:
                provision_brew(stage)
                commit_stage(root, stage, original, activation, replace_tree=True)


def initialize(root, profile_path, check=False):
    if root.exists():
        raise ValueError("Configuration already exists; use finite-home-migrate or finite-home-apply")
    metadata = os.environ.get("FINITE_FOUNDATION_METADATA")
    info = read_json(metadata) if metadata else {}
    profile = json.loads(capture(["yq", "-o=json", ".", str(profile_path)]))
    import pwd
    account = pwd.getpwuid(os.getuid())
    supplied = profile.get("identity", {})
    identity = {"username": account.pw_name, "homeDirectory": account.pw_dir}
    if any(value and value != identity.get(key) for key, value in supplied.items()):
        raise ValueError("Provisioned identity differs from the current account")
    profile.update(schema=2, identity=identity)
    profile.setdefault("packages", [])
    with locked(root):
        with tempfile.TemporaryDirectory(prefix=".foundation-init-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            make_template(source_root(), info, stage)
            validate_profile(profile, catalog_data())
            write_json(stage / "profile.json", profile)
            activation = build(stage)
            if not check:
                provision_brew(stage)
                commit_stage(root, stage, None, activation)


def apply(root, roles=None, packages=None, check=False):
    lock = read_json(root / "flake.lock")
    importing = "foundation" in lock["nodes"][lock["root"]].get("inputs", {})
    if not importing and not (root / "foundation.json").exists():
        raise ValueError("Legacy configuration: run finite-home-migrate first")
    with locked(root):
        original = tree_digest(root)
        with tempfile.TemporaryDirectory(prefix=".foundation-apply-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            copy_configuration(root, stage)
            if importing and not (stage / "foundation.json").exists():
                info = installed_info(root)
                write_json(stage / "foundation.json", info)
                write_json(stage / "finite-template.json", {"schema": 1, "generator": "finite-home-init", "version": info["version"]})
            profile = read_json(stage / "profile.json")
            for field, value in (("roles", roles), ("packages", packages)):
                if value is not None:
                    profile[field] = value.split(",") if value else []
            validate_profile(profile, catalog_data())
            write_json(stage / "profile.json", profile)
            activation = build(stage)
            if not check:
                provision_brew(stage)
                commit_stage(root, stage, original, activation)


def status(root, machine=False, notify=False, review=False):
    lock = read_json(root / "flake.lock")
    if "foundation" not in lock["nodes"][lock["root"]].get("inputs", {}):
        result = {"migration_required": True, "update_available": False}
        print(json.dumps(result) if machine else "Legacy Home Manager configuration: run finite-home-migrate to adopt Foundation")
        return
    installed, candidate, _ = available(root)
    result = {"migration_required": False, "installed_version": installed["version"], "installed_rev": installed["rev"],
              "update_available": candidate is not None, "available_version": candidate["version"] if candidate else None}
    text = f"Installed Foundation: {installed['version']}\n" + (f"Available Foundation: {candidate['version']}\nRun ujust update or finite-home-update to build and apply it." if candidate else "No newer published Foundation release is available.")
    print(json.dumps(result) if machine else text)
    if notify and candidate:
        state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "foundation"
        marker = state / "notified-release"
        if marker.exists() and marker.read_text().strip() == candidate["rev"]:
            return
        selected = capture(["notify-send", "--app-name=Foundation", "--action=default=Review update", "--action=review=Review update", "--wait", "--expire-time=0", "Foundation update available", text])
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        marker.write_text(candidate["rev"] + "\n")
        review = selected in ("default", "review")
    if review:
        result = subprocess.run(["zenity", "--text-info", "--title=Foundation updates", "--width=700", "--height=400"], input=text, text=True)
        if result.returncode not in (0, 1):
            raise ValueError("Could not display the Foundation update review")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("update", "migrate", "init", "apply"):
        item = sub.add_parser(command)
        item.add_argument("--check", action="store_true")
        if command == "init":
            item.add_argument("--profile", required=True, type=Path)
        if command == "apply":
            item.add_argument("--roles")
            item.add_argument("--packages")
    item = sub.add_parser("status")
    for flag in ("json", "notify", "review"):
        item.add_argument("--" + flag, action="store_true")
    item = sub.add_parser("template")
    for field in ("source", "metadata", "output"):
        item.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "template":
            make_template(args.source, read_json(args.metadata), args.output)
            return 0
        if args.command != "status" and os.geteuid() == 0:
            raise ValueError("Run Foundation configuration commands as the desktop user, not root")
        root = config_root()
        if args.command == "update":
            update(root, args.check)
        elif args.command == "migrate":
            releases = published_releases()
            if not releases:
                raise ValueError("No published Foundation releases are available")
            info, lock = release_data(releases[-1][1])
            migrate(root, info, lock, args.check)
        elif args.command == "init":
            initialize(root, args.profile, args.check)
        elif args.command == "apply":
            apply(root, args.roles, args.packages, args.check)
        else:
            status(root, args.json, args.notify, args.review)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"Foundation: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
