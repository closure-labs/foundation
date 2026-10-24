# Bundle only files used by the installed Python helpers. Source revision/NAR
# metadata still describes the complete release, independently of this bundle.
source: let
  root = toString source;
  files = [
    "VERSION" "foundation.json" "flake.lock" "legacy-managed.json"
    "profile.json" "customize.nix" "modules/local.nix" "scripts/home.py"
    "LICENSE" "NOTICE" "ORIGIN.md"
  ];
  parents = ["modules" "scripts"];
in
  builtins.path {
    name = "foundation-helper-source";
    path = source;
    filter = path: type: let
      relative = builtins.substring (builtins.stringLength root + 1) (builtins.stringLength (toString path)) (toString path);
    in
      toString path == root
      || builtins.elem relative files
      || (type == "directory" && builtins.elem relative parents)
      || relative == "lib"
      || builtins.substring 0 4 relative == "lib/";
  }
