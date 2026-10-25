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
    flakeModules.aspects = ../../home/construction/_aspects.nix;
    homeConfigurations.${profile.identity.username} = home;
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
