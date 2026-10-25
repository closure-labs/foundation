{
  "id" = "apps/icebox";
  "metadata" = {
    "application" = {
      "declaration" = "flatpak:flathub:io.github.pleromix.IceBox";
      "graphical" = true;
      "id" = "io.github.pleromix.IceBox";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:io.github.pleromix.IceBox";
      "graphical" = true;
      "id" = "io.github.pleromix.IceBox";
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
        id = "icebox";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
