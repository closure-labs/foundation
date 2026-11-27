{
  description = "Finite's default Home Manager flake: a Foundation for reproducible Linux workstations";

  outputs = {self, ...} @ args: let
    pins = (import ./.tack) {overrides = args.tackOverrides or {};};
    inputs = builtins.removeAttrs pins ["_meta" "_patched" "__functor"] // {inherit self;};
  in
    inputs.flake-parts.lib.mkFlake {inherit inputs;} (inputs.import-tree ./modules);
}
