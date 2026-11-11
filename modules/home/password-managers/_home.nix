{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.foundation.passwordManagers;
  candidates = lib.unique (
    builtins.filter (package: lib.getName package == "1password") config.home.packages
  );
  selected =
    if cfg.onePassword.package != null then
      cfg.onePassword.package
    else if candidates == [ ] then
      null
    else
      builtins.head candidates;
  enabled = cfg.enable && selected != null;
  integration = import ./_package.nix {
    inherit pkgs lib;
    nixpkgsSource = inputs.nixpkgs.outPath;
    package = selected;
  };
  base = {
    name = "com.1password.1password";
    description = "1Password BrowserSupport";
    path = integration.hostPath;
    type = "stdio";
  };
  firefoxManifest = base // {
    allowed_extensions = [
      "{0a75d802-9aed-41e7-8daa-24c067386e82}"
      "{25fc87fa-4d31-4fee-b5c1-c32a7844c063}"
      "{d634138d-c276-4fc8-924b-40a0ea21d284}"
    ];
  };
  chromiumManifest = base // {
    allowed_origins = map (id: "chrome-extension://${id}/") [
      "hjlinigoblmkhjejkmbegnoaljkphmgo"
      "bkpbhnjcbehoklfkljkkbbmipaphipgl"
      "gejiddohjgogedgjnonbofjigllpkmbf"
      "khgocmkkpikpnmmkgmdnfckapcdkgfaf"
      "aeblfdkhhhdcdjpifhhbdiojplfjncoa"
      "dppgmdbiimibapkepcbdbmkaabgiofem"
    ];
  };
in
{
  options.foundation.passwordManagers = {
    enable = lib.mkEnableOption "provider-aware password-manager integration" // {
      default = true;
    };
    onePassword.package = lib.mkOption {
      type = lib.types.nullOr lib.types.package;
      default = null;
      description = "Explicit Nix 1Password GUI package; null detects it from home.packages, including nixGL wrapping.";
    };
    onePassword.requirement = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = if enabled then integration.requirement else null;
      readOnly = true;
      description = "Immutable host requirement for explicit administrator review and installation; null without the GUI package.";
    };
  };
  config = lib.mkMerge [
    {
      assertions = [
        {
          assertion = !cfg.enable || cfg.onePassword.package != null || builtins.length candidates <= 1;
          message = "Multiple Nix 1Password GUI packages detected; select foundation.passwordManagers.onePassword.package explicitly.";
        }
      ];
    }
    (lib.mkIf enabled {
      home.file.".mozilla/native-messaging-hosts/com.1password.1password.json".text =
        builtins.toJSON firefoxManifest;
      xdg.configFile."chromium/NativeMessagingHosts/com.1password.1password.json".text =
        builtins.toJSON chromiumManifest;
      home.extraBuilderCommands = lib.mkAfter ''
        ln -s ${integration.requirement} "$out/foundation-password-managers.json"
      '';
    })
  ];
}
