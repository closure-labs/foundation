{
  "id" = "apps/pinta";
  "metadata" = {
    "application" = {
      "attribute" = "pinta";
      "declaration" = "nix:nixpkgs:pinta";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:com.github.PintaProject.Pinta";
      "graphical" = true;
      "id" = "com.github.PintaProject.Pinta";
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
        id = "pinta";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
