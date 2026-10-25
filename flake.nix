# DO-NOT-EDIT. This file was auto-generated using github:vic/flake-file.
# Use `nix run .#write-flake` to regenerate it.
{
  description = "Finite's default Home Manager flake: a Foundation for reproducible Linux workstations";

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules);

  inputs = {
    den.url = "github:denful/den";
    determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/3";
    devenv.url = "github:cachix/devenv/v2.2.2";
    flake-file.url = "github:vic/flake-file/619d2212482c104fd3bbc815d80c6227b1b01338";
    flake-parts = {
      inputs.nixpkgs-lib.follows = "determinate/nix/nixpkgs";
      url = "https://flakehub.com/f/hercules-ci/flake-parts/0.1";
    };
    gen = {
      inputs.nixpkgs.follows = "nixpkgs";
      url = "github:sini/gen/6427d42770e3b1c283b8caf2929ed622e551ebb9";
    };
    home-manager = {
      inputs.nixpkgs.follows = "nixpkgs";
      url = "https://flakehub.com/f/nix-community/home-manager/0.2605";
    };
    import-tree.url = "github:denful/import-tree/a164a12202f58eb67559bd33b5592f20660d9baf";
    nix-flatpak.url = "github:gmodena/nix-flatpak";
    nixGL = {
      inputs.nixpkgs.follows = "nixpkgs";
      url = "github:nix-community/nixGL";
    };
    nixpkgs.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-26.05-chilled/0.1";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nixpkgs-weekly.url = "https://flakehub.com/f/DeterminateSystems/nixpkgs-weekly/0.1";
  };

}
