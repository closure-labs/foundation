{
  "id" = "apps/gearlever";
  "metadata" = {
    "application" = {
      "attribute" = "gearlever";
      "declaration" = "nix:nixpkgs:gearlever";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "removeIconBuildFiles" = true;
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:it.mijorus.gearlever";
      "graphical" = true;
      "id" = "it.mijorus.gearlever";
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
        id = "gearlever";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
