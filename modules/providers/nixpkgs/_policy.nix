{ lib }: value: let
  evaluated = lib.evalModules {
    modules = [{
      options.packagePolicy = lib.mkOption {
        default = {};
        type = lib.types.submodule {
          options = {
            unfree = lib.mkOption {
              type = lib.types.enum ["allow" "deny" "allowlist"];
              default = "allow";
              description = "License policy for all Foundation-owned Nixpkgs channels.";
            };
            allowedUnfreePackages = lib.mkOption {
              type = lib.types.listOf (lib.types.addCheck lib.types.str (name: name != ""));
              default = [];
              description = "Version-independent package names permitted in allowlist mode.";
            };
          };
        };
      };
      config.packagePolicy = value;
    }];
  };
  policy = evaluated.config.packagePolicy;
in
  builtins.deepSeq policy (
    if policy.unfree != "allow" && builtins.getEnv "NIXPKGS_ALLOW_UNFREE" == "1" then
      throw "Foundation packagePolicy requires NIXPKGS_ALLOW_UNFREE to be unset in restrictive modes; Nixpkgs otherwise bypasses deny/allowlist during impure evaluation"
    else if policy.unfree != "allowlist" && policy.allowedUnfreePackages != [] then
      throw "Foundation packagePolicy.allowedUnfreePackages requires packagePolicy.unfree = \"allowlist\""
    else policy
  )
