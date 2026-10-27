{
  "id" = "apps/distroshelf";
  "metadata" = {
    "application" = {
      "attribute" = "distroshelf";
      "declaration" = "nix:nixpkgs:distroshelf";
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
      id = "distroshelf";
      application = (import ./_feature.nix).metadata.application;
    });
}
