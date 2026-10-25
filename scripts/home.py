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
import signal
import shutil
import selectors
import time
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path

REPOSITORY = "closure-labs/foundation"
COMPATIBILITY = 1
RELEASE_CHANNEL = "latest-release"
CORE = {"den", "gen", "devenv", "nixpkgs", "nixpkgs-weekly", "nixpkgs-unstable", "home-manager", "determinate", "nix-flatpak", "nixGL"}
EXCLUDED = {".git", ".jj", ".agents", ".aws", ".codex", ".direnv", ".devenv", "result"}
REFERENCE = re.compile(r'^(\s*(?:inputs\.)?foundation\.url = ")github:closure-labs/foundation/(latest-release|[a-f0-9]{40}|v[0-9]+\.[0-9]+\.[0-9]+)(";)$', re.MULTILINE)


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, **kwargs)


def capture(command):
    return run(command, stdout=subprocess.PIPE).stdout.strip()



def download_retryable(output):
    """416 is transient only after this command interrupted the same URL."""
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    terminal = (r"HTTP (?:error |response:? )?4(?!(?:08|16|29)\b)[0-9]{2}\b|"
                r"hash mismatch|NAR hash mismatch|signature.*(?:invalid|failed)|does not match expected hash|"
                r"error:[^\n]*\b(?:signature|hash|authentication)\b|"
                r"(?:not signed|no signatures|untrusted public key)|"
                r"unauthorized|forbidden|permission denied|"
                r"\b(?:SIGKILL|SIGTERM|SIGINT|Killed|Out of memory|oom-kill(?:ed)?|terminated by signal)\b|"
                r"syntax error|undefined variable|attribute .* missing|infinite recursion|assertion .* failed|"
                r"evaluation (?:aborted|failed)|cannot evaluate|Reason: builder failed|"
                r"builder (?:for .*? failed|failed) with exit code")
    if re.search(terminal, output, re.I):
        return False
    interrupted = re.compile(r"unable to download '([^'\n]+)': [^\n]*"
                             r"(?:partial file|receiving data|sending data)[^\n]*"
                             r"retrying from offset [1-9][0-9]*", re.I)
    ranges = list(re.finditer(r"unable to download '([^'\n]+)': HTTP error 416\b", output, re.I))
    transient = (r"HTTP (?:error |response:? )?(?:408|429|500|502|503|504)\b|"
                 r"(?:could not|couldn't) resolve (?:host|hostname)|"
                 r"(?:connection|network) (?:reset|timed out|is unreachable)|"
                 r"Transferred a partial file|Failure when receiving data|"
                 r"Temporary failure in name resolution|TLS connect error")
    # A transient transfer elsewhere in the log must not hide an evaluation,
    # local-store or unrelated build error. Permit only transfer diagnostics and
    # Nix's known substitute/dependency cascade; unknown root errors fail closed.
    for error in re.finditer(r"^[ \t]*error: ([^\n]*(?:\n[ \t]+(?![ \t]*error:)[^\n]*)*)", output, re.M | re.I):
        message = error[1]
        if re.match(r"unable to download\b", message, re.I):
            if re.search(transient, message, re.I) or re.search(r"HTTP error 416\b", message, re.I):
                continue
        elif (re.fullmatch(r"path '[^'\n]+' is required, but there is no substituter that can build it", message)
              or re.fullmatch(r"some substitutes for the outputs of derivation '[^'\n]+' failed \(usually happens due to networking issues\); try '--fallback' to build derivation from source", message)
              or (re.match(r"Cannot build '[^'\n]+\.drv'\.\n", message)
                  and re.search(r"^\s+Reason: [1-9][0-9]* dependenc(?:y|ies) failed\.$", message, re.M))):
            continue
        return False
    if re.search(r"HTTP (?:error |response:? )?416\b", output, re.I):
        return bool(ranges) and all(any(previous[1] == failure[1]
            for previous in interrupted.finditer(output[:failure.start()])) for failure in ranges)
    return bool(re.search(transient, output, re.I))


def build_attempt(command, timeout):
    """Stream diagnostics and bound the whole process group, including nested retries."""
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) as process:
        with selectors.DefaultSelector() as ready:
            ready.register(process.stdout, selectors.EVENT_READ, "stdout")
            ready.register(process.stderr, selectors.EVENT_READ, "stderr")
            deadline = time.monotonic() + timeout
            try:
                while ready.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    for key, _ in ready.select(min(remaining, 1)):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            ready.unregister(key.fileobj)
                            continue
                        name = key.data
                        captured[name].extend(chunk)
                        if name == "stderr":
                            sys.stderr.write(chunk.decode("utf-8", errors="replace"))
                            sys.stderr.flush()
                            # Lack of retained proof makes an old 416 terminal.
                            del captured[name][:-8 * 1024 * 1024]
                        elif len(captured[name]) > 65536:
                            raise ValueError("Oversized realization output")
                status = process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except BaseException:
                # systemd-run --scope and its Nix descendants share this new
                # process group. Never leave inner download retries running.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
    return subprocess.CompletedProcess(command, status,
        captured["stdout"].decode("utf-8", errors="replace"),
        captured["stderr"].decode("utf-8", errors="replace"))


def capture_build(command, *, clock=None, sleep=None, execute=None):
    """Retry realization only; configuration generation and activation run once."""
    clock, sleep, execute = clock or time.monotonic, sleep or time.sleep, execute or build_attempt
    deadline = clock() + 900
    for attempt in range(1, 4):
        remaining = deadline - clock()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, 900)
        result = execute(command, remaining)
        if clock() > deadline:
            raise subprocess.TimeoutExpired(command, 900)
        if result.returncode == 0:
            return result.stdout.strip()
        if result.returncode != 1 or attempt == 3 or not download_retryable(result.stderr):
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        delay = 2 * attempt
        if clock() + delay >= deadline:
            raise subprocess.TimeoutExpired(command, 900)
        print(f"Foundation: transient realization download failure; retry {attempt + 1}/3 in {delay}s", file=sys.stderr)
        sleep(delay)
    raise AssertionError("Unreachable realization retry state")


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_staged_profile(stage, profile):
    # Replace the directory entry so a copied symlink cannot write into live data.
    with tempfile.NamedTemporaryFile(prefix=".profile-", dir=stage, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        write_json(temporary, profile)
        temporary.replace(stage / "profile.json")
    finally:
        temporary.unlink(missing_ok=True)


def replace_file_entry(source, destination):
    """Copy a file or symlink as an entry, without following either live path."""
    with tempfile.NamedTemporaryFile(prefix=".foundation-entry-", dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
    temporary.unlink()
    try:
        shutil.copy2(source, temporary, follow_symlinks=False)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def config_root():
    return Path(os.environ.get("FINITE_HOME_FLAKE_PATH", str(Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "home-manager")))


def source_root():
    return Path(os.environ.get("FINITE_FOUNDATION_SOURCE", Path(__file__).resolve().parents[1]))


def validate_capabilities(value):
    fields = ("initializeSchemas", "normalizeSchemas", "catalogSchemas")
    if (not isinstance(value, dict) or type(value.get("schema")) is not int or value["schema"] != 1
            or any(not isinstance(value.get(field), list) or not value[field]
                   or any(type(item) is not int or item < 1 for item in value[field])
                   or len(set(value[field])) != len(value[field]) for field in fields)
            or type(value.get("writeSchema")) is not int
            or value["writeSchema"] not in value["initializeSchemas"]
            or value["writeSchema"] not in value["normalizeSchemas"]):
        raise ValueError("Invalid Foundation profile capabilities")
    if "editSchemas" in value:
        supported = value["editSchemas"]
        if (not isinstance(supported, list) or not supported
                or any(type(item) is not int or item not in value["normalizeSchemas"] for item in supported)
                or len(set(supported)) != len(supported)):
            raise ValueError("Invalid Foundation profile editing capabilities")
    return value


def profile_capabilities():
    # Describe the running helper, never a source selected through environment.
    return validate_capabilities(read_json(Path(__file__).resolve().parents[1] / "lib/profile-capabilities.json"))


def require_helper_schema(profile, field="normalizeSchemas"):
    if (not isinstance(profile, dict) or type(profile.get("schema")) is not int
            or profile["schema"] not in profile_capabilities()[field]):
        raise ValueError("The installed Foundation helper does not support this profile schema")


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


def foundation_reference(reference):
    key = "rev" if re.fullmatch(r"[a-f0-9]{40}", reference) else "ref"
    return {"type": "github", "owner": "closure-labs", "repo": "foundation", key: reference}


def consumer_lock(lock, info, reference=RELEASE_CHANNEL):
    """Re-root a release's committed graph; follows paths belong to its old root."""
    validate_metadata(info)
    old_root = lock["root"]
    names = {name: "foundation" if name == old_root else "foundation-" + name for name in lock["nodes"]}
    def rebase_reference(ref):
        return ["foundation", *ref] if isinstance(ref, list) else names[ref]
    nodes = {}
    for name, node in lock["nodes"].items():
        node = copy.deepcopy(node)
        if "inputs" in node:
            node["inputs"] = {key: rebase_reference(ref) for key, ref in node["inputs"].items()}
        nodes[names[name]] = node
    nodes["foundation"].update({
        "locked": {"type": "github", "owner": "closure-labs", "repo": "foundation",
                   **{key: info[key] for key in ("rev", "narHash", "lastModified") if key in info}},
        "original": foundation_reference(reference),
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
    if "nixGL" in inputs:
        raise ValueError("A legacy input named nixGL requires manual migration to preserve its personal pin and followers")
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


def consumer_flake(info, extras=None, reference=RELEASE_CHANNEL):
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
'''.replace("REVISION", reference).replace("EXTRAS", extra_text)


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
        destination = output / relative
        if not destination.exists() and not destination.is_symlink():
            shutil.copy2(source / relative, destination)
            # Store sources are read-only; personal configuration must be editable.
            destination.chmod(destination.stat().st_mode | 0o200)


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
    """Schema-2 fallback for selected releases without a Nix normalizer."""
    if not isinstance(profile, dict) or type(profile.get("schema")) is not int or profile["schema"] != 2:
        raise ValueError("Unsupported profile schema; migrate a schema-1 profile with the existing initializer first")
    for field, choices in (("roles", catalog["roles"]), ("packages", catalog["packages"])):
        requested = profile.get(field)
        if (not isinstance(requested, list) or any(not isinstance(x, str) or x not in choices for x in requested)
                or len(set(requested)) != len(requested)):
            raise ValueError(f"Invalid or duplicate {field}")
        profile[field] = sorted(requested, key=lambda x: (choices[x]["order"], x))
    if any(not isinstance(profile.get(field), str) or profile[field] not in catalog[choices]
           for field, choices in (("foundation", "foundations"), ("hardware", "hardware"))):
        raise ValueError("Unsupported host foundation or hardware")
    identity = profile.get("identity", {})
    if (not isinstance(identity, dict) or not isinstance(identity.get("username"), str)
            or not re.fullmatch(r"[a-z_][a-z0-9_-]*[$]?", identity["username"])
            or not isinstance(identity.get("homeDirectory"), str)
            or not re.fullmatch(r"/.+", identity["homeDirectory"])):
        raise ValueError("Invalid account identity")
    return profile


def validate_runtime_profile(profile, catalog):
    """Account and running-image checks belong to the invoking machine."""
    identity = profile["identity"]
    import pwd
    if identity["username"] != pwd.getpwuid(os.getuid()).pw_name or Path(identity["homeDirectory"]).resolve() != Path.home().resolve():
        raise ValueError("Profile identity must match the invoking desktop user")
    running = Path(os.environ.get("FINITE_RUNNING_PROFILE_PATH", "/usr/share/finite/profile.json"))
    if running.exists():
        host = read_json(running)
        if profile["foundation"] != host["foundation"] or host["hardware"] not in catalog["hardware"][profile["hardware"]]["imageHardware"]:
            raise ValueError("Profile is incompatible with the running Finite image")


def validate_staged_profile(stage, data=None):
    # Read the profile from the same staged flake as its locked Foundation.
    # Fallback is capability-based: target validation failures must propagate.
    submitted = read_json(stage / "profile.json")
    require_helper_schema(submitted)
    expression = 'let root = builtins.getFlake ' + nix_value("path:" + str(stage)) + ''';
      target = root.inputs.foundation or root;
      submitted = builtins.fromJSON (builtins.readFile (root.outPath + "/profile.json"));
      hasNormalizer = target.lib ? normalizeProfile;
      hasCapabilities = target.lib ? profileCapabilities;
    in {
      inherit hasNormalizer;
      catalog = if target.lib ? homeCatalogForSchema then target.lib.homeCatalogForSchema submitted.schema else target.lib.homeCatalog;
      profile = if submitted.schema == 3 && !hasCapabilities
        then throw "Schema 3 requires explicit selected Foundation capabilities"
        else if hasCapabilities && !(builtins.elem submitted.schema target.lib.profileCapabilities.normalizeSchemas)
        then throw "Selected Foundation does not support this profile schema"
        else if hasNormalizer then target.lib.normalizeProfile submitted else submitted;
    } // (if hasCapabilities then { capabilities = target.lib.profileCapabilities; } else {})'''
    if data is None:
        data = json.loads(capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
    if submitted["schema"] == 3 and "capabilities" not in data:
        raise ValueError("Schema 3 requires explicit selected Foundation capabilities")
    profile = data["profile"]
    require_helper_schema(profile)
    if profile.get("schema") != submitted["schema"]:
        raise ValueError("Selected Foundation changed the profile schema during normalization")
    if (type(data["catalog"].get("schema")) is not int
            or data["catalog"]["schema"] not in profile_capabilities()["catalogSchemas"]):
        raise ValueError("The installed Foundation helper does not support this catalog schema")
    if "capabilities" in data:
        capabilities = validate_capabilities(data["capabilities"])
        if submitted["schema"] not in capabilities["normalizeSchemas"] or data["catalog"]["schema"] not in capabilities["catalogSchemas"]:
            raise ValueError("Selected Foundation capabilities do not support this profile or catalog schema")
    if not data["hasNormalizer"]:
        profile = validate_profile(profile, data["catalog"])
    validate_runtime_profile(profile, data["catalog"])
    return profile


def editor_target(stage, schema, change=None):
    """Resolve editor data from the staged locked target, never the caller catalog."""
    require_helper_schema(read_json(stage / "profile.json"))
    if schema not in profile_capabilities().get("editSchemas", [2]):
        raise ValueError("The installed Foundation helper does not support editing this profile schema")
    request = {"schema": schema, "change": change}
    expression = 'let root = builtins.getFlake ' + nix_value("path:" + str(stage)) + ''';
      target = root.inputs.foundation or root;
      submitted = builtins.fromJSON (builtins.readFile (root.outPath + "/profile.json"));
      request = builtins.fromJSON REQUEST;
      hasNormalizer = target.lib ? normalizeProfile;
      hasCapabilities = target.lib ? profileCapabilities;
      hasEditor = (target.lib.profileChanges.schema or 0) == 1;
      supported = if hasCapabilities then target.lib.profileCapabilities.editSchemas or [2] else [2];
      canEdit = hasEditor && builtins.elem request.schema supported;
      catalogFor = schema: if target.lib ? homeCatalogForSchema then target.lib.homeCatalogForSchema schema else target.lib.homeCatalog;
    in {
      inherit hasNormalizer;
      catalog = catalogFor submitted.schema;
      profile = if submitted.schema == 3 && !hasCapabilities then throw "Schema 3 requires explicit selected Foundation capabilities"
        else if hasCapabilities && !(builtins.elem submitted.schema target.lib.profileCapabilities.normalizeSchemas)
        then throw "Selected Foundation does not support this profile schema"
        else if hasNormalizer then target.lib.normalizeProfile submitted else submitted;
      editorCatalog = if request.schema == 3 && (!canEdit || !(target.lib ? homeCatalogForSchema))
        then throw "Selected Foundation does not support schema-3 editing; update Foundation first"
        else catalogFor request.schema;
      source = { path = toString target.outPath; narHash = target.narHash or null; rev = target.rev or null; };
      editorSchema = if hasEditor then 1 else 0;
      canMigrate = hasEditor && builtins.elem 3 supported && (target.lib ? homeCatalogForSchema);
      preview = if request.change == null then null
        else if !canEdit then throw "Selected Foundation does not support profile change previews"
        else target.lib.profileChanges.preview ({ profile = submitted; } // request.change);
    } // (if hasCapabilities then { capabilities = target.lib.profileCapabilities; } else {})'''
    expression = expression.replace("REQUEST", nix_value(json.dumps(request)))
    data = json.loads(capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
    normalized = validate_staged_profile(stage, data)
    if change is not None and data.get("editorSchema") != 1:
        raise ValueError("Selected Foundation does not support this profile preview API")
    if schema not in profile_capabilities().get("editSchemas", [2]):
        raise ValueError("The installed Foundation helper does not support editing this profile schema")
    if schema == 3 and (data.get("editorSchema") != 1 or 3 not in data.get("capabilities", {}).get("editSchemas", [2])):
        raise ValueError("Selected Foundation does not advertise schema-3 editing")
    catalog = data["editorCatalog"]
    if type(catalog.get("schema")) is not int or catalog["schema"] not in profile_capabilities()["catalogSchemas"]:
        raise ValueError("The installed Foundation helper does not support this editor catalog")
    return {**data, "profile": normalized}


def profile_hash(root):
    # tree_digest records a symlink's destination, not the linked profile bytes.
    return hashlib.sha256((root / "profile.json").read_bytes()).hexdigest()


def selection_change(roles, packages, capabilities, migrate):
    return {"roles": None if roles is None else (roles.split(",") if roles else []),
            "packages": None if packages is None else (packages.split(",") if packages else []),
            "capabilities": None if capabilities is None else (capabilities.split(",") if capabilities else []),
            "migrate": migrate}


def preview_summary(preview):
    if preview["status"] == "blocked":
        return preview["reason"]
    changes = preview["changes"]
    candidate = preview["candidate"]
    lines = [f"Profile format: {preview['source']['schema']} → {candidate['schema']}",
             "Roles: " + (", ".join(candidate["roles"]) or "none"),
             "Additional capabilities: " + (", ".join(candidate.get("capabilities", [])) or "none"),
             "Optional packages: " + (", ".join(candidate["packages"]) or "none")]
    for label, field in (("Applications added", "addedApplications"), ("Applications no longer declared", "removedApplications")):
        lines.append(label + ": " + (", ".join(changes[field]) or "none"))
    if "host" in candidate:
        host = candidate["host"]
        lines.insert(1, f"Host: {host['formFactor']}; CPU: {host['cpu']}; GPUs: {', '.join(host['gpus']) or 'none declared'}; model: {host['model']}")
    if changes["providerChanges"]:
        lines.append("Application source changes:")
        for row in changes["providerChanges"]:
            before = "Flathub" if row["before"].startswith("flatpak:") else "Nixpkgs"
            after = "Flathub" if row["after"].startswith("flatpak:") else "Nixpkgs"
            lines.append(f"  {row['application']}: {before} ({row['before'].split(':')[-1]}) → {after} ({row['after'].split(':')[-1]})")
    if changes["graphics"]["before"] != changes["graphics"]["after"]:
        lines.append("Graphical Nix apps will use nixGL (Mesa). Validate graphics and application behavior on this host.")
    lines.extend(["Existing Flatpak apps may remain installed. Application data is kept.",
                  "Nix apps do not automatically import data from their Flatpak versions.",
                  "Both versions may appear in the application launcher; check which version you open.",
                  "This preview covers Foundation selections; personal modules can add or override applications."])
    return "\n\n".join(lines)


def prepare_profile_change(stage, root, original, raw_profile_hash, change):
    submitted = read_json(stage / "profile.json")
    require_helper_schema(submitted)
    schema = 3 if change["migrate"] else submitted.get("schema")
    data = editor_target(stage, schema, change)
    preview = data["preview"]
    if not isinstance(preview, dict) or preview.get("status") not in ("preview", "blocked") or preview.get("activationAllowed") is not False:
        raise ValueError("Invalid selected Foundation profile preview")
    if preview.get("source") != data["profile"]:
        raise ValueError("Selected Foundation preview does not match the source profile")
    if preview["status"] == "preview":
        candidate = preview["candidate"]
        require_helper_schema(candidate)
        if candidate["schema"] != schema:
            raise ValueError("Selected Foundation preview changed the requested schema")
        for key, value in data["profile"].items():
            if key not in ("schema", "roles", "packages", "capabilities") and candidate.get(key) != value:
                raise ValueError("Selected Foundation preview changed a preserved profile field")
    result = {"schema": 1, "preview": preview, "source": data["source"], "summary": preview_summary(preview)}
    binding = {"root": str(root.resolve()), "tree": original, "profileHash": raw_profile_hash,
               "lockHash": hashlib.sha256((stage / "flake.lock").read_bytes()).hexdigest(),
               "change": change, "result": result}
    result["approvalToken"] = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def read_editor(root, *, migrate=False, preview=False, roles=None, packages=None, capabilities=None):
    """Read-only commands use /tmp staging and never create a consumer lock file."""
    original = tree_digest(root)
    raw_hash = profile_hash(root)
    with tempfile.TemporaryDirectory(prefix="foundation-profile-preview-") as temporary:
        stage = Path(temporary) / "home-manager"
        copy_configuration(root, stage)
        submitted = read_json(stage / "profile.json")
        require_helper_schema(submitted)
        if migrate and submitted.get("schema") != 2:
            raise ValueError("Explicit profile conversion requires a schema-2 source")
        for field in ("capabilities", "host"):
            if migrate and field in submitted:
                raise ValueError(f"Existing custom {field} field collides with schema 3; resolve it explicitly before migration")
        if capabilities is not None and submitted.get("schema") == 2 and not migrate:
            raise ValueError("Capabilities require explicit --migrate-profile conversion to schema 3")
        if preview:
            result = prepare_profile_change(stage, root, original, raw_hash, selection_change(roles, packages, capabilities, migrate))
        else:
            schema = 3 if migrate else read_json(stage / "profile.json").get("schema")
            data = editor_target(stage, schema)
            result = {"schema": 1, "profile": data["profile"], "catalog": data["editorCatalog"],
                      "canMigrate": data["canMigrate"] and 3 in profile_capabilities().get("editSchemas", [2])}
        if tree_digest(root) != original or profile_hash(root) != raw_hash:
            raise ValueError("Configuration changed while reading the editor; try again")
        return result


def build(stage):
    memory_max = os.environ.get("FOUNDATION_BUILD_MEMORY_MAX", "5G")
    if not re.fullmatch(r"[1-9][0-9]*[MG]", memory_max):
        raise ValueError("FOUNDATION_BUILD_MEMORY_MAX must be a positive M or G budget, such as 5G")
    submitted = read_json(stage / "profile.json")
    profile = validate_staged_profile(stage)
    if profile != submitted:
        write_staged_profile(stage, profile)
    installable = f"path:{stage}#homeConfigurations.{profile['identity']['username']}.activationPackage"
    command = ["systemd-run", "--user", "--scope", "--quiet", "-p", "MemoryMax=" + memory_max, "-p", "MemorySwapMax=512M", "-p", "CPUQuota=100%",
               "nix", "build", "--max-jobs", "1", "--cores", "1", "--no-update-lock-file", "--no-link", "--print-out-paths", installable]
    try:
        paths = capture_build(command).splitlines()
    except subprocess.CalledProcessError as error:
        if error.returncode != -signal.SIGKILL:
            raise
        raise ValueError(
            f"Home Manager build was killed (SIGKILL) with MemoryMax={memory_max}. "
            "Check the user journal for an out-of-memory event; if confirmed, "
            "retry with a larger FOUNDATION_BUILD_MEMORY_MAX budget. Nothing was activated."
        ) from error
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
      bootstrap = builtins.readFile (f.outPath + "/modules/_legacy/finite-brew-bootstrap");
      status = builtins.readFile (f.outPath + "/modules/_legacy/finite-brew-migration-status");
      policy = builtins.readFile (f.outPath + "/modules/_legacy/aspects/base/brew-packages.json");
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


def commit_stage(root, stage, original, activation, replace_tree=False, expected_profile_hash=None, replace_customization=False):
    if (tree_digest(root) if root.exists() else None) != original:
        raise ValueError("Configuration changed during the build; nothing installed")
    if expected_profile_hash is not None and profile_hash(root) != expected_profile_hash:
        raise ValueError("Profile changed during the build; nothing installed")
    previous = previous_generation()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = root.with_name(root.name + ".previous." + stamp)
    consumer = root.exists() and not replace_tree
    committed_files = ("flake.nix", "flake.lock", "foundation.json", "finite-template.json", "profile.json")
    # An explicitly reviewed workstation conversion can include its GUI bindings.
    # Ordinary updates and role edits leave this user-owned module untouched.
    if replace_customization:
        committed_files += ("customize.nix",)
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
                replace_file_entry(stage / relative, root / relative)
        run([str(activation / "activate")])
    except BaseException:
        failed = root.with_name(root.name + ".failed." + stamp)
        if consumer:
            copy_configuration(root, failed)
            for relative in committed_files:
                if (backup / relative).exists() or (backup / relative).is_symlink():
                    replace_file_entry(backup / relative, root / relative)
                else:
                    (root / relative).unlink(missing_ok=True)
        else:
            root.rename(failed)
            if backup.exists():
                backup.rename(root)
        if previous is not None:
            try:
                run([str(previous / "activate")])
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
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


def local_foundation_source(source):
    if source.get("type") != "git" or not isinstance(source.get("url"), str):
        return False
    url = urllib.parse.urlsplit(source["url"])
    return (url.scheme == "file" and not url.netloc and url.path.startswith("/")
            and not url.query and not url.fragment)


def foundation_source(root):
    lock = read_json(root / "flake.lock")
    reference = lock["nodes"][lock["root"]]["inputs"]["foundation"]
    node = lock["nodes"][reference]
    source = node["locked"]
    published = (source.get("type") == "github" and source.get("owner") == "closure-labs"
                 and source.get("repo") == "foundation")
    if not published and not local_foundation_source(source):
        raise ValueError("Personal Foundation input points to another repository or unsupported source")
    if local_foundation_source(source) and node.get("original", {}).get("rev") != source.get("rev"):
        raise ValueError("Local Foundation input must explicitly pin its locked Git revision")
    return source


def installed_info(root):
    # nh/nix can update the lock without rewriting our cached provenance file.
    # Always identify the selected source from the consumer lock first.
    source = foundation_source(root)
    provenance = {key: source[key] for key in ("rev", "narHash", "lastModified") if key in source}
    # Validate the revision before constructing a reference from it.
    if not re.fullmatch(r"[a-f0-9]{40}", provenance.get("rev") or ""):
        raise ValueError("Foundation lock must contain an immutable Git commit")
    if local_foundation_source(source):
        if not re.fullmatch(r"sha256-[A-Za-z0-9+/]{43}=", provenance.get("narHash") or ""):
            raise ValueError("Local Foundation lock must contain a content hash")
        expression = 'let root = builtins.getFlake ' + nix_value("path:" + str(root.resolve())) + ''';
          target = root.inputs.foundation;
        in {
          metadata = builtins.fromJSON (builtins.readFile (target.outPath + "/foundation.json"));
          rev = target.rev; narHash = target.narHash; lastModified = target.lastModified or 0;
        }'''
        selected = json.loads(capture(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression]))
        if any(selected.get(key) != value for key, value in provenance.items()):
            raise ValueError("Selected local Foundation differs from its locked source")
        installed = {**selected["metadata"], **{key: selected[key] for key in ("rev", "narHash", "lastModified")}}
        validate_metadata(installed)
        return installed
    installed = read_json(root / "foundation.json") if (root / "foundation.json").exists() else {}
    if any(installed.get(key) != value for key, value in provenance.items()):
        expression = 'let f = builtins.getFlake ' + json.dumps(f"github:{REPOSITORY}/{source['rev']}") + '; in builtins.fromJSON (builtins.readFile (f.outPath + "/foundation.json"))'
        installed = json.loads(capture(["nix", "eval", "--json", "--expr", expression]))
    installed = {**installed, **provenance}
    validate_metadata(installed)
    return installed


def available(root):
    installed = installed_info(root)
    if local_foundation_source(foundation_source(root)):
        return installed, None, None
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
            if local_foundation_source(foundation_source(root)):
                print(f"Foundation {installed['version']} is pinned to a local checkout ({installed['rev'][:12]}). "
                      "Advance the foundation input explicitly, then run finite-home-apply. No published-release update applied.")
            else:
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
            if len(matches) != 1 or matches[0][2] not in (RELEASE_CHANNEL, installed["rev"], "v" + installed["version"]):
                raise ValueError("The Foundation input was customized; update it manually")
            tracking = matches[0][2] == RELEASE_CHANNEL
            text = REFERENCE.sub(lambda m: m[1] + f"github:{REPOSITORY}/{info['rev']}" + m[3], text)
            (stage / "flake.nix").write_text(text)
            # Nix updates this input closure only, retaining personal input pins.
            run(["nix", "flake", "lock", "path:" + str(stage)])
            new_lock = read_json(stage / "flake.lock")
            verify_update_lock(read_json(root / "flake.lock"), new_lock, lock, info)
            selected = new_lock["nodes"][new_lock["nodes"][new_lock["root"]]["inputs"]["foundation"]]["locked"]
            if selected["rev"] != info["rev"] or selected["narHash"] != info["narHash"]:
                raise ValueError("Resolved Foundation source differs from the reviewed release")
            if tracking:
                # Resolve/build the reviewed immutable release, retaining the channel
                # declaration for the next nh update. Both locked graphs are identical.
                (stage / "flake.nix").write_text(REFERENCE.sub(
                    lambda m: m[1] + f"github:{REPOSITORY}/{RELEASE_CHANNEL}" + m[3], text))
                reference = new_lock["nodes"][new_lock["root"]]["inputs"]["foundation"]
                new_lock["nodes"][reference]["original"] = foundation_reference(RELEASE_CHANNEL)
                write_json(stage / "flake.lock", new_lock)
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
    if (not isinstance(profile, dict) or type(profile.get("schema")) is not int
            or profile["schema"] not in profile_capabilities()["initializeSchemas"]):
        raise ValueError("Unsupported profile schema for this initializer")
    import pwd
    account = pwd.getpwuid(os.getuid())
    supplied = profile.get("identity", {})
    if not isinstance(supplied, dict):
        raise ValueError("Invalid provisioned identity")
    identity = {"username": account.pw_name, "homeDirectory": account.pw_dir}
    if any(supplied.get(key) and supplied[key] != value for key, value in identity.items()):
        raise ValueError("Provisioned identity differs from the current account")
    if profile["schema"] == 1:
        profile["schema"] = 2
        profile.setdefault("packages", [])
    profile["identity"] = {**supplied, **identity}
    with locked(root):
        with tempfile.TemporaryDirectory(prefix=".foundation-init-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            make_template(source_root(), info, stage)
            write_staged_profile(stage, profile)
            activation = build(stage)
            if not check:
                provision_brew(stage)
                commit_stage(root, stage, None, activation)


def apply(root, roles=None, packages=None, check=False, capabilities=None, migrate_profile=False, preview=False, approve_preview=None):
    if preview:
        return read_editor(root, migrate=migrate_profile, preview=True, roles=roles, packages=packages, capabilities=capabilities)
    if approve_preview is not None and not re.fullmatch(r"[a-f0-9]{64}", approve_preview):
        raise ValueError("Invalid preview token; request a fresh --preview")
    lock = read_json(root / "flake.lock")
    importing = "foundation" in lock["nodes"][lock["root"]].get("inputs", {})
    if not importing and not (root / "foundation.json").exists():
        raise ValueError("Legacy configuration: run finite-home-migrate first")
    with locked(root):
        original = tree_digest(root)
        raw_hash = profile_hash(root)
        with tempfile.TemporaryDirectory(prefix=".foundation-apply-", dir=root.parent) as temp:
            stage = Path(temp) / "home-manager"
            copy_configuration(root, stage)
            if importing:
                info = installed_info(root)
                write_json(stage / "foundation.json", info)
                write_json(stage / "finite-template.json", {"schema": 1, "generator": "finite-home-init", "version": info["version"]})
            profile = read_json(stage / "profile.json")
            require_helper_schema(profile)
            if profile.get("schema") == 3 or capabilities is not None or migrate_profile or approve_preview is not None:
                change = selection_change(roles, packages, capabilities, migrate_profile)
                result = prepare_profile_change(stage, root, original, raw_hash, change)
                if result["preview"]["status"] == "blocked":
                    raise ValueError(result["preview"]["reason"])
                if approve_preview is not None and approve_preview != result["approvalToken"]:
                    raise ValueError("Preview is stale or selections changed; request a fresh --preview")
                if migrate_profile and approve_preview is None and not check:
                    raise ValueError("Conversion requires a reviewed --preview; repeat with --approve-preview TOKEN")
                profile = result["preview"]["candidate"]
            else:
                for field, value in (("roles", roles), ("packages", packages)):
                    if value is not None:
                        profile[field] = value.split(",") if value else []
            if tree_digest(root) != original or profile_hash(root) != raw_hash:
                raise ValueError("Configuration changed while preparing the profile; nothing built")
            write_staged_profile(stage, profile)
            activation = build(stage)
            if tree_digest(root) != original or profile_hash(root) != raw_hash:
                raise ValueError("Configuration changed during the build; nothing installed")
            if not check:
                provision_brew(stage)
                commit_stage(root, stage, original, activation, expected_profile_hash=raw_hash)


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
    if local_foundation_source(foundation_source(root)):
        result.update(source="local-git", update_policy="manual-pin")
        text = (f"Installed Foundation: {installed['version']} ({installed['rev'][:12]})\n"
                "Pinned local checkout. Advance the foundation input explicitly, then run finite-home-apply. "
                "Published releases were not checked.")
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


def generate_profile(args):
    """Generate data through the bundled pure validator; no consumer or flake evaluation."""
    import pwd
    account = pwd.getpwuid(os.getuid())
    def csv(value):
        return value.split(",") if value else []
    submitted = {"schema": 3, "foundation": args.foundation,
                 "roles": csv(args.roles), "packages": csv(args.packages), "capabilities": csv(args.capabilities),
                 "identity": {"username": account.pw_name, "homeDirectory": account.pw_dir}}
    if args.hardware is not None:
        submitted["hardware"] = args.hardware
    host = {field: getattr(args, field) for field in ("system", "cpu", "model", "camera", "fingerprint")
            if getattr(args, field) is not None}
    if args.form_factor is not None:
        host["formFactor"] = args.form_factor
    if args.gpus is not None:
        host["gpus"] = csv(args.gpus)
    bundled = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="foundation-profile-") as temporary:
        profile_file = Path(temporary) / "profile.json"
        host_file = Path(temporary) / "host.json"
        write_json(profile_file, submitted)
        write_json(host_file, host)
        checked = json.loads(capture(["nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", str(bundled / "lib/generate-profile.nix"),
                                      "--argstr", "profileFile", str(profile_file), "--argstr", "hostFile", str(host_file)]))
    if os.environ.get("FINITE_SKIP_FOUNDATION_CHECK") != "true":
        validate_runtime_profile(checked["profile"], {"hardware": checked["hardware"]})
    return checked["profile"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    item = sub.add_parser("profile", help="Generate a schema-3 Home Manager profile")
    item.add_argument("--foundation", required=True)
    for name in ("roles", "packages", "capabilities"):
        item.add_argument("--" + name, default="", help="Comma-separated selections")
    for name in ("hardware", "system", "form-factor", "cpu", "gpus", "model"):
        item.add_argument("--" + name)
    for name in ("camera", "fingerprint"):
        item.add_argument("--" + name, action=argparse.BooleanOptionalAction, default=None)
    item.add_argument("--format", choices=("json", "yaml"), default="yaml")
    for command in ("update", "migrate", "init", "apply"):
        item = sub.add_parser(command)
        item.add_argument("--check", action="store_true")
        if command == "init":
            selection = item.add_mutually_exclusive_group(required=True)
            selection.add_argument("--profile", type=Path)
            selection.add_argument("--capabilities", action="store_true")
        if command == "apply":
            item.add_argument("--roles")
            item.add_argument("--packages")
            item.add_argument("--capabilities")
            item.add_argument("--migrate-profile", action="store_true")
            mode = item.add_mutually_exclusive_group()
            mode.add_argument("--preview", action="store_true")
            mode.add_argument("--editor-context", action="store_true")
            item.add_argument("--approve-preview")
    item = sub.add_parser("status")
    for flag in ("json", "notify", "review"):
        item.add_argument("--" + flag, action="store_true")
    item = sub.add_parser("template")
    for field in ("source", "metadata", "output"):
        item.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "profile":
            payload = json.dumps(generate_profile(args), indent=2, sort_keys=True) + "\n"
            if args.format == "yaml":
                payload = run(["yq", "-P"], input=payload, stdout=subprocess.PIPE).stdout
            print(payload, end="")
            return 0
        if args.command == "init" and args.capabilities:
            print(json.dumps(profile_capabilities(), sort_keys=True))
            return 0
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
            if args.editor_context:
                if args.roles is not None or args.packages is not None or args.capabilities is not None or args.approve_preview or args.check:
                    raise ValueError("--editor-context only accepts --migrate-profile")
                print(json.dumps(read_editor(root, migrate=args.migrate_profile), sort_keys=True))
            else:
                if args.preview and (args.approve_preview is not None or args.check):
                    raise ValueError("--preview cannot be combined with --approve-preview or --check")
                result = apply(root, args.roles, args.packages, args.check, args.capabilities, args.migrate_profile, args.preview, args.approve_preview)
                if args.preview:
                    print(json.dumps(result, sort_keys=True))
        else:
            status(root, args.json, args.notify, args.review)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"Foundation: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
