{ inputs, ... }: {
  imports = [ inputs.flake-file.flakeModules.default ];
  systems = [ "x86_64-linux" ];
  flake-file = {
    description = "Finite's default Home Manager flake: a Foundation for reproducible Linux workstations";
    prune-lock.enable = false;
    outputs = "inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules)";
    inputs = {
      den.url = "github:denful/den";
      # Match the repository's tested hub and deduplicate its sibling libraries.
      gen.url = "github:sini/gen/6427d42770e3b1c283b8caf2929ed622e551ebb9";
      gen.inputs.nixpkgs.follows = "nixpkgs";

      flake-parts.inputs.nixpkgs-lib.follows = "determinate/nix/nixpkgs";
      flake-parts.url = "https://flakehub.com/f/hercules-ci/flake-parts/0.1";
      import-tree.url = "github:denful/import-tree/a164a12202f58eb67559bd33b5592f20660d9baf";
      flake-file.url = "github:vic/flake-file/619d2212482c104fd3bbc815d80c6227b1b01338";

    };
  };
}
