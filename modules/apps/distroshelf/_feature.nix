{
  "id" = "apps/distroshelf";
  "metadata" = {
    "application" = {
      "attribute" = "distroshelf";
      "declaration" = "nix:nixpkgs:distroshelf";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:com.ranfdev.DistroShelf";
      "graphical" = true;
      "id" = "com.ranfdev.DistroShelf";
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
        id = "distroshelf";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
