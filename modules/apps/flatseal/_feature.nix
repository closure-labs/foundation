{
  "id" = "apps/flatseal";
  "metadata" = {
    "application" = {
      "declaration" = "flatpak:flathub:com.github.tchx84.Flatseal";
      "graphical" = true;
      "id" = "com.github.tchx84.Flatseal";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ "providers/flatpak" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "flatseal";
      application = (import ./_feature.nix).metadata.application;
    });
}
