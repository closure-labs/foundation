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
      foundation = applications.foundation;
      default = applications.foundation;
      home-apply = applications.homeApply;
      home-manager-template = api.mkConsumerTemplate {inherit pkgs;};
      home-profile-catalog = pkgs.writeText "home-profile-catalog.json" (builtins.toJSON api.homeCatalog);
      home-profile = applications.homeProfile;
      home-init = applications.homeInit;
      home-bootstrap = applications.homeBootstrap;
      home-update = applications.homeUpdate;
      home-migrate = applications.homeMigrate;
      app-status = applications.appStatus;
    };
    apps.${system} = let
      app = package: { type = "app"; program = pkgs.lib.getExe package; };
    in {
      default = app applications.foundation;
      foundation = app applications.foundation;
      home-profile = app applications.homeProfile;
      home-init = app applications.homeInit;
      home-bootstrap = app applications.homeBootstrap;
      home-check = app (pkgs.writeShellApplication {
        name = "foundation-home-check";
        text = ''exec ${applications.foundation}/bin/foundation home check "$@"'';
      });
      home-apply = app applications.homeApply;
      home-update = app applications.homeUpdate;
      home-migrate = app applications.homeMigrate;
      home-configure = app applications.configure;
      home-camera = app applications.camera;
      app-status = app applications.appStatus;
    };
    templates.default = {
      path = ../../../templates/default;
      description = "Personal Home Manager flake importing Foundation";
    };
    devShells.${system}.ci = pkgs.mkShellNoCC {
      packages = with pkgs; [bash jq python3 actionlint yq-go];
    };
  }
