{
  "id" = "apps/gnome-chess";
  "metadata" = {
    "application" = {
      "attribute" = "gnome-chess";
      "declaration" = "nix:nixpkgs:gnome-chess";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "gnome-chess";
      "declaration" = "nix:nixpkgs:gnome-chess";
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
        id = "gnome-chess";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
