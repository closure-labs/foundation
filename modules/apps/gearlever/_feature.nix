{
  "id" = "apps/gearlever";
  "metadata" = {
    "application" = {
      "attribute" = "gearlever";
      "declaration" = "nix:nixpkgs:gearlever";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "removeIconBuildFiles" = true;
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
      id = "gearlever";
      application = (import ./_feature.nix).metadata.application;
    });
}
