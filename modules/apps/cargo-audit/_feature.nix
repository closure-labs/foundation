{
  "id" = "apps/cargo-audit";
  "metadata" = {
    "application" = {
      "attribute" = "cargo-audit";
      "declaration" = "nix:nixpkgs:cargo-audit";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "cargo-audit";
      application = (import ./_feature.nix).metadata.application;
    });
}
