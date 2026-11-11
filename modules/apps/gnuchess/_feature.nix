{
  "id" = "apps/gnuchess";
  "metadata" = {
    "application" = {
      "attribute" = "gnuchess";
      "declaration" = "nix:nixpkgs:gnuchess";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "gnuchess";
      application = (import ./_feature.nix).metadata.application;
    });
}
