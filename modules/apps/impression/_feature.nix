{
  "id" = "apps/impression";
  "metadata" = {
    "application" = {
      "attribute" = "impression";
      "declaration" = "nix:nixpkgs:impression";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:io.gitlab.adhami3310.Impression";
      "graphical" = true;
      "id" = "io.gitlab.adhami3310.Impression";
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
        id = "impression";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
