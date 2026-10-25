{
  "id" = "apps/herdr";
  "metadata" = {
    "application" = {
      "attribute" = "herdr";
      "declaration" = "nix:nixpkgs-unstable:herdr";
      "graphical" = false;
      "input" = "nixpkgs-unstable";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "herdr";
      "declaration" = "nix:nixpkgs-unstable:herdr";
      "graphical" = false;
      "input" = "nixpkgs-unstable";
      "provider" = "nix";
    };
    "package" = {
      "description" = "Terminal process manager";
      "label" = "Herdr";
      "name" = "herdr";
      "order" = 20;
    };
  };
  "dependencies" = [ "providers/nixpkgs-unstable" ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "herdr";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
