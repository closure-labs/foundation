{
  description = "Finite's default Home Manager flake: a Foundation for reproducible Linux workstations";

  # Keep dependency pins in flake.lock under version control.
  # Den passes these inputs to customize.nix and modules/local.nix.
  inputs = {
    den.url = "github:denful/den";
    # Match the repository's tested hub and deduplicate its sibling libraries.
    gen.url = "github:sini/gen/6427d42770e3b1c283b8caf2929ed622e551ebb9";
    gen.inputs.nixpkgs.follows = "nixpkgs";
    devenv.url = "github:cachix/devenv/v2.2.2";
    nixpkgs.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1";
    nixpkgs-weekly.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/0.1";
    # Keep Herdr fixes independent of the shared desktop package pins.
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    home-manager = {
      url = "https://flakehub.com/f/nix-community/home-manager/0.2605";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/3";
    nix-flatpak.url = "github:gmodena/nix-flatpak";
    nixGL = {
      url = "github:nix-community/nixGL";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs: let
    system = "x86_64-linux";
    pkgs = inputs.nixpkgs.legacyPackages.${system};
    api = import ./lib {inherit inputs;};
    profile = builtins.fromJSON (builtins.readFile ./profile.json);
    home = api.mkHomeConfiguration {
      inherit profile;
      modules = [./customize.nix ./modules/local.nix];
    };
    applications = api.mkApplications {inherit pkgs;};
  in {
    lib = api;
    flakeModules.aspects = ./modules/aspects.nix;
    homeConfigurations.${profile.identity.username} = home;
    checks.${system} = {
      home = home.activationPackage;
      profile-command =
        pkgs.runCommand "foundation-profile-command" {
          nativeBuildInputs = with pkgs; [bash coreutils];
        } ''
          bash ${./tests/profile-command.sh} \
            ${pkgs.writeText "install-packages.sh" home.config.home.activation.installPackages.data} \
            ${pkgs.lib.escapeShellArg home.config.home.profileDirectory}
          touch "$out"
        '';
      nixgl-wrapper = import ./tests/nixgl-wrapper.nix {foundation = inputs.self;};
      desktop-icons = import ./tests/icon-packages.nix {foundation = inputs.self;};
      profile-generation =
        pkgs.runCommand "foundation-profile-generation" {
          nativeBuildInputs = with pkgs; [bash coreutils jq yq-go];
        } ''
          bash ${./tests/profile-generation.sh} ${applications.homeProfile}/bin/finite-home-profile ${applications.profileCatalog}
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
      path = ./templates/default;
      description = "Personal Home Manager flake importing Foundation";
    };
    devShells.${system}.ci = pkgs.mkShellNoCC {
      packages = with pkgs; [bash jq python3 actionlint yq-go];
    };
  };
}
