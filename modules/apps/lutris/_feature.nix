{
  "id" = "apps/lutris";
  "metadata" = {
    "application" = {
      "attribute" = "lutris";
      "declaration" = "nix:nixpkgs:lutris";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [
    "providers/nixpkgs"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "lutris";
      application = (import ./_feature.nix).metadata.application;
    });
}
