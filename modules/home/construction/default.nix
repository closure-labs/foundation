{ ... }: {
  flake-file.inputs.home-manager = {
    url = "https://flakehub.com/f/nix-community/home-manager/0.2605";
    inputs.nixpkgs.follows = "nixpkgs";
  };
}
