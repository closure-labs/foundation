{
  "id" = "apps/camera-controls";
  "metadata" = {
    "application" = {
      "attribute" = "cameractrls";
      "declaration" = "nix:nixpkgs:cameractrls";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:hu.irl.cameractrls";
      "graphical" = true;
      "id" = "hu.irl.cameractrls";
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
        id = "camera-controls";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
