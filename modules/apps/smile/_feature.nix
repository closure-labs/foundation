{
  "id" = "apps/smile";
  "metadata" = {
    "application" = {
      "attribute" = "smile";
      "declaration" = "nix:nixpkgs:smile";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "removeIconBuildFiles" = true;
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:it.mijorus.smile";
      "graphical" = true;
      "id" = "it.mijorus.smile";
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
        id = "smile";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
