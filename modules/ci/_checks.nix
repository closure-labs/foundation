{ inputs }:
let
  system = "x86_64-linux";
  pkgs = inputs.nixpkgs.legacyPackages.${system};
  api = inputs.self.lib;
  profile = builtins.fromJSON (builtins.readFile ../../profile.json);
  home = inputs.self.homeConfigurations.${profile.identity.username};
  applications = api.mkApplications {
    inherit pkgs;
    releaseInfo = { };
  };
in
{
  home = home.activationPackage;
  # Build the actual exported constructor. Fixture metadata keeps path:.
  # checks pure while still exercising the packaged Python module context.
  consumer-template = api.mkConsumerTemplate {
    inherit pkgs;
    releaseInfo = {
      inherit (api.sourceInfo) version;
      schema = 1;
      compatibility = 1;
      rev = "0000000000000000000000000000000000000000";
      narHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
  };
  profile-command =
    pkgs.runCommand "foundation-profile-command"
      {
        nativeBuildInputs = with pkgs; [
          bash
          coreutils
        ];
      }
      ''
        bash ${../../tests/profile-command.sh} \
          ${pkgs.writeText "install-packages.sh" home.config.home.activation.installPackages.data} \
          ${pkgs.lib.escapeShellArg home.config.home.profileDirectory}
        touch "$out"
      '';
  nixgl-wrapper = import ../../tests/nixgl-wrapper.nix { foundation = inputs.self; };
  desktop-icons = import ../../tests/icon-packages.nix { foundation = inputs.self; };
  profile-generation =
    pkgs.runCommand "foundation-profile-generation"
      {
        nativeBuildInputs = with pkgs; [
          bash
          coreutils
          jq
          yq-go
        ];
      }
      ''
        bash ${../../tests/profile-generation.sh} ${applications.homeProfile}/bin/foundation-home-profile ${applications.profileCatalog}
        bash ${../../tests/foundation-cli.sh} ${applications.foundation}/bin/foundation
        touch "$out"
      '';
}
