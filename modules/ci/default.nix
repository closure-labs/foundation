{ inputs, ... }: {
  perSystem =
    { pkgs, ... }:
    let
      graph = builtins.toJSON (import ./_graph.nix);
      diagram = pkgs.writeText "foundation-architecture.md" (import ./_diagram.nix);
      generated = pkgs.writeText "foundation-ci-graph.json" (graph + "\n");
      plans = import ./_plans.nix;
      publicChecks = builtins.attrNames inputs.self.checks.${pkgs.stdenv.hostPlatform.system};
    in
    {
      packages.write-ci-graph = pkgs.writeShellApplication {
        name = "write-ci-graph";
        text = "cp ${generated} modules/ci/_graph.json\ncp ${diagram} docs/ARCHITECTURE.md";
      };
      checks = (import ./_checks.nix { inherit inputs; }) // {
        ci-graph =
          assert builtins.sort builtins.lessThan plans.full.checks == builtins.sort builtins.lessThan publicChecks;
          assert builtins.all (name: builtins.elem name publicChecks) plans.automation.checks;
          pkgs.runCommand "foundation-ci-graph" { } ''
          cmp ${generated} ${./_graph.json}
          cmp ${diagram} ${../../docs/ARCHITECTURE.md}
          touch "$out"
        '';
      };
    };
}
