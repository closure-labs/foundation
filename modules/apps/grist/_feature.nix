{
  "id" = "apps/grist";
  "metadata" = {
    "application" = {
      "declaration" = "desktop-entry:finite-grist";
      "graphical" = false;
      "name" = "finite-grist";
      "provider" = "desktop-entry";
    };
  };
  "dependencies" = [ "providers/desktop-entry" ];
  "schemaDependencies" = { };
  configuration = schema: {
    imports = [
      ./_settings.nix
      (import ../../profiles/composition/_application.nix {
        id = "grist";
        application = (import ./_feature.nix).metadata.application;
      })
    ];
  };
}
