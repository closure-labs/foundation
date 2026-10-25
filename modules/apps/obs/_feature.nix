{
  "id" = "apps/obs";
  "metadata" = {
    "application" = {
      "attribute" = "obs-studio";
      "declaration" = "nix:nixpkgs:obs-studio";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "obs-studio";
      "declaration" = "nix:nixpkgs:obs-studio";
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
        id = "obs";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
