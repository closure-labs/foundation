{
  "id" = "apps/devenv";
  "metadata" = {
    "application" = {
      "attribute" = "devenv";
      "declaration" = "nix:devenv:devenv";
      "graphical" = false;
      "input" = "devenv";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/devenv" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "devenv";
      application = (import ./_feature.nix).metadata.application;
    });
}
