# Evaluate without building proprietary software; build only an inert helper and
# the real pinned native security wrapper. Physical browser integration is separate.
{ foundation }:
let
  pkgs = foundation.inputs.nixpkgs.legacyPackages.x86_64-linux;
  inherit (pkgs) lib;
  fake =
    version:
    pkgs.runCommand "1password-${version}"
      {
        pname = "1password";
        inherit version;
      }
      ''
        mkdir -p "$out/share/1password"
        cp ${pkgs.hello}/bin/hello "$out/share/1password/1Password-BrowserSupport"
      '';
  gui = fake "1";
  wrapped = pkgs.symlinkJoin {
    name = "1password-1";
    paths = [ gui ];
  };
  cli = pkgs.runCommand "1password-cli-1" { } "mkdir -p $out";
  evaluate =
    packages: extra:
    (lib.evalModules {
      specialArgs = {
        inherit pkgs;
        inputs = foundation.inputs;
      };
      modules = [
        {
          options = {
            home.packages = lib.mkOption {
              type = lib.types.listOf lib.types.package;
              default = [ ];
            };
            home.file = lib.mkOption {
              type = lib.types.attrs;
              default = { };
            };
            home.extraBuilderCommands = lib.mkOption {
              type = lib.types.lines;
              default = "";
            };
            xdg.configFile = lib.mkOption {
              type = lib.types.attrs;
              default = { };
            };
            assertions = lib.mkOption {
              type = lib.types.listOf lib.types.attrs;
              default = [ ];
            };
          };
        }
        ../modules/home/password-managers/_home.nix
        { home.packages = packages; }
        extra
      ];
    }).config;
  absent = evaluate [ ] { };
  cliOnly = evaluate [ cli ] { };
  plain = evaluate [ gui ] { };
  selected = evaluate [ wrapped ] { };
  ambiguous = evaluate [ gui (fake "2") ] { };
  explicit = evaluate [ gui (fake "2") ] {
    foundation.passwordManagers.onePassword.package = wrapped;
  };
  disabled = evaluate [ gui ] { foundation.passwordManagers.enable = false; };
  allValid = c: builtins.all (a: a.assertion) c.assertions;
  fx =
    builtins.fromJSON
      selected.home.file.".mozilla/native-messaging-hosts/com.1password.1password.json".text;
  chromium =
    builtins.fromJSON
      selected.xdg.configFile."chromium/NativeMessagingHosts/com.1password.1password.json".text;
  contract = {
    absentNoRequirement = absent.foundation.passwordManagers.onePassword.requirement == null;
    absentNoManifests = absent.home.file == { } && absent.xdg.configFile == { };
    cliNoRequirement = cliOnly.foundation.passwordManagers.onePassword.requirement == null;
    disabledNoRequirement = disabled.foundation.passwordManagers.onePassword.requirement == null;
    plainDetected = plain.foundation.passwordManagers.onePassword.requirement != null;
    wrappedDetected = selected.foundation.passwordManagers.onePassword.requirement != null;
    ambiguousRejected = !allValid ambiguous;
    explicitResolvesAmbiguity = allValid explicit;
    sameVersionedHost =
      fx.path == chromium.path && lib.hasPrefix "/var/lib/finite/password-managers/1password/" fx.path;
    expectedFirefoxOrigins =
      builtins.length fx.allowed_extensions == 3
      && builtins.elem "{d634138d-c276-4fc8-924b-40a0ea21d284}" fx.allowed_extensions;
    expectedChromiumOrigins =
      builtins.length chromium.allowed_origins == 6
      && builtins.elem "chrome-extension://aeblfdkhhhdcdjpifhhbdiojplfjncoa/" chromium.allowed_origins;
    noElevation = !lib.hasInfix "sudo" selected.home.extraBuilderCommands;
  };
  requirement = selected.foundation.passwordManagers.onePassword.requirement;
in
{
  inherit contract;
  build =
    assert builtins.all (value: value) (builtins.attrValues contract);
    pkgs.runCommand "foundation-password-manager-contract"
      {
        nativeBuildInputs = [
          pkgs.jq
          pkgs.coreutils
          pkgs.binutils
        ];
      }
      ''
        jq -e --arg package ${lib.escapeShellArg (toString wrapped)} --arg helper ${lib.escapeShellArg "${gui}/share/1password/1Password-BrowserSupport"} '
          .schema == 1 and .manager == "1password" and .package == $package and
          .helper == $helper and (.helperSha256 | test("^[a-f0-9]{64}$")) and
          (.wrapperSha256 | test("^[a-f0-9]{64}$")) and
          (.wrapper | startswith("/nix/store/")) and
          (.hostPath | startswith("/var/lib/finite/password-managers/1password/"))
        ' ${requirement} >/dev/null
        wrapper=$(jq -r .wrapper ${requirement})
        helper=$(jq -r .helper ${requirement})
        test "$(sha256sum "$helper" | cut -d ' ' -f 1)" = "$(jq -r .helperSha256 ${requirement})"
        test "$(sha256sum "$wrapper" | cut -d ' ' -f 1)" = "$(jq -r .wrapperSha256 ${requirement})"
        # A real native ELF, statically linked, with the exact selected target.
        readelf -h "$wrapper" >/dev/null
        if readelf -l "$wrapper" | grep -q INTERP; then exit 1; fi
        test ! -u "$wrapper" && test ! -g "$wrapper"
        # Nix sandboxes may not implement security.capability xattrs on /proc/self/exe.
        # Keep the inert wrapper available for the separate host execution check.
        mkdir "$out"
        ln -s ${requirement} "$out/requirement.json"
      '';
}
