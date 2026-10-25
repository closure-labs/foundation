{
  "id" = "apps/ignition";
  "metadata" = {
    "application" = {
      "attribute" = "ignition";
      "declaration" = "nix:nixpkgs:ignition";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:io.github.flattool.Ignition";
      "graphical" = true;
      "id" = "io.github.flattool.Ignition";
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
        id = "ignition";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
