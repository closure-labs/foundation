{
  "id" = "apps/rustconn";
  "metadata" = {
    "application" = {
      "declaration" = "flatpak:flathub:io.github.totoshko88.RustConn";
      "graphical" = true;
      "id" = "io.github.totoshko88.RustConn";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ "providers/flatpak" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "rustconn";
      application = (import ./_feature.nix).metadata.application;
    });
}
