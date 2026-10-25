{
  "id" = "apps/chromium";
  "metadata" = {
    "application" = {
      "attribute" = "chromium";
      "declaration" = "nix:nixpkgs:chromium";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:org.chromium.Chromium";
      "graphical" = true;
      "id" = "org.chromium.Chromium";
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
        id = "chromium";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
