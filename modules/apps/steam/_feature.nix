{
  "id" = "apps/steam";
  "metadata" = {
    "application" = {
      "attribute" = "steam";
      "declaration" = "nix:nixpkgs:steam";
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
      id = "steam";
      application = (import ./_feature.nix).metadata.application;
    });
}
