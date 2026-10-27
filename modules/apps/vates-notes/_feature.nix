{
  "id" = "apps/vates-notes";
  "metadata" = {
    "application" = {
      "declaration" = "desktop-entry:finite-vates-notes";
      "graphical" = false;
      "name" = "finite-vates-notes";
      "provider" = "desktop-entry";
    };
  };
  "dependencies" = [ "providers/desktop-entry" ];
  "schemaDependencies" = { };
  configuration = schema: {
    imports = [
      ./_settings.nix
      (import ../../profiles/composition/_application.nix {
        id = "vates-notes";
        application = (import ./_feature.nix).metadata.application;
      })
    ];
  };
}
