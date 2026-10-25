{
  "id" = "apps/refine";
  "metadata" = {
    "application" = {
      "attribute" = "refine";
      "declaration" = "nix:nixpkgs:refine";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:page.tesk.Refine";
      "graphical" = true;
      "id" = "page.tesk.Refine";
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
        id = "refine";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
