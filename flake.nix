{
  description = "Finite's default Home Manager flake: a Foundation for reproducible Linux workstations";

  # Keep dependency pins in flake.lock under version control.
  # Den passes these inputs to customize.nix and modules/local.nix.
  inputs = {
    den.url = "github:denful/den";
    # Match the repository's tested hub and deduplicate its sibling libraries.
    gen.url = "github:sini/gen/0004f3c9dfd5634f47ee72575e56c54883450bcf";
    gen.inputs.nixpkgs.follows = "nixpkgs";
    devenv.url = "github:cachix/devenv/v2.2.2";
    nixpkgs.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1";
    nixpkgs-weekly.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/0.1";
    home-manager = {
      url = "https://flakehub.com/f/nix-community/home-manager/0.2605";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/3";
    nix-flatpak.url = "github:gmodena/nix-flatpak";
  };

  outputs = inputs: let
    system = "x86_64-linux";
    pkgs = inputs.nixpkgs.legacyPackages.${system};
    flake = (inputs.nixpkgs.lib.evalModules {
      specialArgs = {inherit inputs;};
      modules = [
        inputs.den.flakeModule
        ./modules/finite.nix
      ];
    }).config.flake;
  in
    flake // {
      checks.x86_64-linux = builtins.mapAttrs (_: home: home.activationPackage) flake.homeConfigurations;
      devShells.${system}.ci = pkgs.mkShellNoCC {
        packages = with pkgs; [bash jq python3 actionlint];
      };
    };
}
