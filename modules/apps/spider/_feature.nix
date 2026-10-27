{
  "id" = "apps/spider";
  "metadata" = {
    "application" = {
      "declaration" = "flatpak:flathub:io.github.zaedus.spider";
      "graphical" = true;
      "id" = "io.github.zaedus.spider";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ "providers/flatpak" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "spider";
      application = (import ./_feature.nix).metadata.application;
    });
}
