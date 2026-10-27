{
  "id" = "apps/warehouse";
  "metadata" = {
    "application" = {
      "attribute" = "warehouse";
      "declaration" = "nix:nixpkgs:warehouse";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "3" = [
      "providers/nixpkgs"
      "providers/graphics"
    ];
  };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "warehouse";
      application = (import ./_feature.nix).metadata.application;
    });
}
