{
  "id" = "apps/thunderbird";
  "metadata" = {
    legacyBaseOrder = 6;
    "application" = {
      "attribute" = "thunderbird";
      "declaration" = "nix:nixpkgs:thunderbird";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
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
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "thunderbird";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
