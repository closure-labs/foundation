{
  "id" = "apps/damask";
  "metadata" = {
    "application" = {
      "declaration" = "flatpak:flathub:app.drey.Damask";
      "graphical" = true;
      "id" = "app.drey.Damask";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:app.drey.Damask";
      "graphical" = true;
      "id" = "app.drey.Damask";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ "providers/flatpak" ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "damask";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
