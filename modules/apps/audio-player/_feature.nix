{
  "id" = "apps/audio-player";
  "metadata" = {
    "application" = {
      "attribute" = "decibels";
      "declaration" = "nix:nixpkgs:decibels";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "decibels";
      "declaration" = "nix:nixpkgs:decibels";
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
        id = "audio-player";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
