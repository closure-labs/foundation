# Reuse the pinned NixOS security wrapper; no privilege bits are set in the store.
{
  pkgs,
  lib,
  nixpkgsSource,
  package,
}:
let
  helper = "${package}/share/1password/1Password-BrowserSupport";
  unsecvars = lib.overrideDerivation (pkgs.srcOnly pkgs.glibc) (
    { name, ... }: {
      name = "${name}-unsecvars";
      installPhase = ''
        mkdir "$out"
        cp sysdeps/generic/unsecvars.h "$out/"
      '';
    }
  );
  nativeWrapper =
    pkgs.pkgsStatic.callPackage (nixpkgsSource + "/nixos/modules/security/wrappers/wrapper.nix")
      {
        sourceProg = helper;
        inherit unsecvars;
      };
  wrapper = pkgs.runCommand "foundation-1password-browser-support" { } ''
    mkdir -p "$out/bin"
    cp ${nativeWrapper}/bin/security-wrapper "$out/bin/1Password-BrowserSupport"
  '';
  hostPath = "/var/lib/finite/password-managers/1password/${builtins.unsafeDiscardStringContext (builtins.baseNameOf wrapper)}/1Password-BrowserSupport";
  requirement =
    pkgs.runCommand "foundation-password-managers.json"
      {
        nativeBuildInputs = [
          pkgs.coreutils
          pkgs.jq
        ];
      }
      ''
        helper=$(readlink -f ${lib.escapeShellArg helper})
        test -f "$helper" && test -x "$helper"
        helper_hash=$(sha256sum "$helper" | cut -d ' ' -f 1)
        wrapper_hash=$(sha256sum ${wrapper}/bin/1Password-BrowserSupport | cut -d ' ' -f 1)
        jq -n --arg package ${lib.escapeShellArg (toString package)} \
          --arg helper "$helper" --arg helperSha256 "$helper_hash" \
          --arg wrapper ${lib.escapeShellArg "${wrapper}/bin/1Password-BrowserSupport"} \
          --arg wrapperSha256 "$wrapper_hash" --arg hostPath ${lib.escapeShellArg hostPath} \
          '{schema: 1, manager: "1password", package: $package, helper: $helper,
            helperSha256: $helperSha256, wrapper: $wrapper, wrapperSha256: $wrapperSha256,
            hostPath: $hostPath}' > "$out"
      '';
in
{
  inherit wrapper requirement hostPath;
}
