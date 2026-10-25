{
  "id" = "apps/mission-center";
  "metadata" = {
    "application" = {
      "attribute" = "mission-center";
      "declaration" = "nix:nixpkgs:mission-center";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:io.missioncenter.MissionCenter";
      "graphical" = true;
      "id" = "io.missioncenter.MissionCenter";
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
        id = "mission-center";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
