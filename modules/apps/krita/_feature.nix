{
  "id" = "apps/krita";
  "metadata" = {
    "application" = {
      "attribute" = "krita";
      "declaration" = "nix:nixpkgs:krita";
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
      id = "krita";
      application = (import ./_feature.nix).metadata.application;
    });
}
