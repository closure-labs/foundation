{
  "id" = "apps/opencode";
  "metadata" = {
    "application" = {
      "attribute" = "opencode";
      "declaration" = "nix:nixpkgs:opencode";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "package" = {
      "description" = "Open-source coding agent";
      "label" = "OpenCode";
      "name" = "opencode";
      "order" = 40;
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "opencode";
      application = (import ./_feature.nix).metadata.application;
    });
}
