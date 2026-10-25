{
  "id" = "apps/gradia";
  "metadata" = {
    "application" = {
      "attribute" = "gradia";
      "declaration" = "nix:nixpkgs:gradia";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:be.alexandervanhee.gradia";
      "graphical" = true;
      "id" = "be.alexandervanhee.gradia";
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
        id = "gradia";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
