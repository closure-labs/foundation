{lib, pkgs, foundationProfileSchema ? 2, ...}: let
  brewPolicy = builtins.fromJSON (builtins.readFile ./_assets/brew-packages.json);
  brewFile = pkgs.writeText "finite.Brewfile" (
    lib.concatMapStrings (tap: "tap ${builtins.toJSON tap.name}, trusted: ${builtins.toJSON tap.trusted}\n") brewPolicy.taps
    + lib.concatMapStrings (package: "brew ${builtins.toJSON package.formula}\n") brewPolicy.packages
  );
  brewMigrationStatus = pkgs.writeShellApplication {
    name = "foundation-brew-status";
    # Absolute helper paths keep the caller's PATH intact for provider checks.
    runtimeEnv = {
      FINITE_BREW_JQ = "${pkgs.jq}/bin/jq";
      FINITE_BREW_READLINK = "${pkgs.coreutils}/bin/readlink";
    };
    text = builtins.readFile ../../home/commands/_assets/finite-brew-migration-status;
  };
in {
  # Homebrew owns the shared CLI tools; this Nix package only checks providers.
  home = {
    packages = lib.mkOrder 700 [brewMigrationStatus];
    activation.checkBrewProviders = lib.hm.dag.entryBefore ["writeBoundary"] ''
      if ! HOMEBREW_NO_AUTO_UPDATE=1 FINITE_BREW_POLICY=${./_assets/brew-packages.json} \
        ${brewMigrationStatus}/bin/foundation-brew-status --check-installed; then
        echo "Install the shared CLI tools before applying this profile:" >&2
        echo "  brew bundle install --no-upgrade --file=${brewFile}" >&2
        exit 1
      fi
    '';
  };

  xdg.configFile = {
    "finite/brew-packages.json".source = ./_assets/brew-packages.json;
    "finite/Brewfile".source = brewFile;
  };
}
