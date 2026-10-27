{
  "id" = "apps/refine";
  "metadata" = {
    "application" = {
      "attribute" = "refine";
      "declaration" = "nix:nixpkgs:refine";
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
      id = "refine";
      application = (import ./_feature.nix).metadata.application;
    });
}
