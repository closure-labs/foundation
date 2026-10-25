{
  "id" = "apps/warehouse";
  "metadata" = {
    "application" = {
      "attribute" = "warehouse";
      "declaration" = "nix:nixpkgs:warehouse";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:io.github.flattool.Warehouse";
      "graphical" = true;
      "id" = "io.github.flattool.Warehouse";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ "providers/flatpak" ];
    "3" = [
      "providers/nixpkgs"
      "providers/graphics"
    ];
  };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "warehouse";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
