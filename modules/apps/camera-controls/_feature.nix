{
  "id" = "apps/camera-controls";
  "metadata" = {
    "application" = {
      "attribute" = "cameractrls";
      "declaration" = "nix:nixpkgs:cameractrls";
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
      id = "camera-controls";
      application = (import ./_feature.nix).metadata.application;
    });
}
