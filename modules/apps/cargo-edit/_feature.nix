{
  "id" = "apps/cargo-edit";
  "metadata" = {
    "application" = {
      "attribute" = "cargo-edit";
      "declaration" = "nix:nixpkgs:cargo-edit";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "cargo-edit";
      application = (import ./_feature.nix).metadata.application;
    });
}
