{ inputs, ... }: {
  systems = [ "x86_64-linux" ];
  perSystem = { system, ... }: {
    _module.args.pkgs = inputs.nixpkgs.legacyPackages.${system};
  };
}
