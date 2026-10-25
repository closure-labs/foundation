{
  "id" = "apps/vlc";
  "metadata" = {
    legacyBaseOrder = 7;
    "application" = {
      "attribute" = "vlc";
      "declaration" = "nix:nixpkgs:vlc";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "vlc";
      "declaration" = "nix:nixpkgs:vlc";
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
        id = "vlc";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
