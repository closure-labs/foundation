{
  "id" = "apps/thunderbird";
  "metadata" = {
    "application" = {
      "attribute" = "thunderbird";
      "declaration" = "nix:nixpkgs:thunderbird";
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
      id = "thunderbird";
      application = (import ./_feature.nix).metadata.application;
    });
}
