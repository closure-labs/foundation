{
  "id" = "apps/mission-center";
  "metadata" = {
    "application" = {
      "attribute" = "mission-center";
      "declaration" = "nix:nixpkgs:mission-center";
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
      id = "mission-center";
      application = (import ./_feature.nix).metadata.application;
    });
}
