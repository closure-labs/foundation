{
  "id" = "apps/cargo-watch";
  "metadata" = {
    "application" = {
      "attribute" = "cargo-watch";
      "declaration" = "nix:nixpkgs:cargo-watch";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "cargo-watch";
      application = (import ./_feature.nix).metadata.application;
    });
}
