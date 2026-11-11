{ inputs, system, packagePolicy ? {} }: let
  inherit (inputs.nixpkgs) lib;
  policy = (import ./_policy.nix { inherit lib; }) packagePolicy;
  config = {
    allowUnfree = policy.unfree == "allow";
    allowUnfreePredicate = package:
      let name = lib.getName package;
      in if policy.unfree == "allow" ||
        (policy.unfree == "allowlist" && builtins.elem name policy.allowedUnfreePackages)
      then true
      else throw ''
        Foundation packagePolicy rejected unfree package '${name}' (mode: ${policy.unfree}).
        Set packagePolicy.unfree = "allow", or use "allowlist" with
        packagePolicy.allowedUnfreePackages in mkHomeConfiguration before package construction.
        Selected applications and services are not silently removed.
      '';
  };
in
  builtins.deepSeq policy (lib.genAttrs ["nixpkgs" "nixpkgs-weekly" "nixpkgs-unstable"] (name:
    import inputs.${name} { inherit system config; }
  ))
