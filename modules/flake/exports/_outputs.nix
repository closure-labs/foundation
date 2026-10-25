inputs: let
    system = "x86_64-linux";
    pkgs = inputs.nixpkgs.legacyPackages.${system};
    api = import ../../../lib {inherit inputs;};
    profile = builtins.fromJSON (builtins.readFile ../../../profile.json);
    home = api.mkHomeConfiguration {
      inherit profile;
      modules = [../../../customize.nix ../../local.nix];
    };
    applications = api.mkApplications {inherit pkgs;};
  in {
    lib = api;
    flakeModules.aspects = ../../_legacy/aspects.nix;
    homeConfigurations.${profile.identity.username} = home;
    checks.${system} = {
      home = home.activationPackage;
      profile-command =
        pkgs.runCommand "foundation-profile-command" {
          nativeBuildInputs = with pkgs; [bash coreutils];
        } ''
          bash ${../../../tests/profile-command.sh} \
            ${pkgs.writeText "install-packages.sh" home.config.home.activation.installPackages.data} \
            ${pkgs.lib.escapeShellArg home.config.home.profileDirectory}
          touch "$out"
        '';
      nixgl-wrapper = import ../../../tests/nixgl-wrapper.nix {foundation = inputs.self;};
      desktop-icons = import ../../../tests/icon-packages.nix {foundation = inputs.self;};
      profile-generation =
        pkgs.runCommand "foundation-profile-generation" {
          nativeBuildInputs = with pkgs; [bash coreutils jq yq-go];
        } ''
          bash ${../../../tests/profile-generation.sh} ${applications.homeProfile}/bin/finite-home-profile ${applications.profileCatalog}
          touch "$out"
        '';
    };
    packages.${system} = {
      home-manager-template = api.mkConsumerTemplate {inherit pkgs;};
      home-profile-catalog = pkgs.writeText "home-profile-catalog.json" (builtins.toJSON api.homeCatalog);
      home-profile = applications.homeProfile;
      home-init = applications.homeInit;
      home-bootstrap = applications.homeBootstrap;
      home-update = applications.homeUpdate;
      home-migrate = applications.homeMigrate;
      app-status = applications.appStatus;
    };
    templates.default = {
      path = ../../../templates/default;
      description = "Personal Home Manager flake importing Foundation";
    };
    devShells.${system}.ci = pkgs.mkShellNoCC {
      packages = with pkgs; [bash jq python3 actionlint yq-go];
    };
  }
