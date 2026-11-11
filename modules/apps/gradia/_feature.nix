{
  "id" = "apps/gradia";
  "metadata" = {
    "application" = {
      "attribute" = "gradia";
      "declaration" = "nix:nixpkgs:gradia";
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
      id = "gradia";
      application = (import ./_feature.nix).metadata.application;
    });
}
