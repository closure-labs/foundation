{
  "id" = "apps/ignition";
  "metadata" = {
    "application" = {
      "attribute" = "ignition";
      "declaration" = "nix:nixpkgs:ignition";
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
      id = "ignition";
      application = (import ./_feature.nix).metadata.application;
    });
}
