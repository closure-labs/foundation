{
  "id" = "apps/joplin";
  "metadata" = {
    "application" = {
      "attribute" = "joplin-desktop";
      "declaration" = "nix:nixpkgs:joplin-desktop";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:net.cozic.joplin_desktop";
      "graphical" = true;
      "id" = "net.cozic.joplin_desktop";
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
        id = "joplin";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
