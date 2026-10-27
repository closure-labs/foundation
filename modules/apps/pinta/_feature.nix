{
  "id" = "apps/pinta";
  "metadata" = {
    "application" = {
      "attribute" = "pinta";
      "declaration" = "nix:nixpkgs:pinta";
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
      id = "pinta";
      application = (import ./_feature.nix).metadata.application;
    });
}
