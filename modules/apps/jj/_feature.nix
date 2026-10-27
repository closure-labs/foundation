{
  "id" = "apps/jj";
  "metadata" = {
    "application" = {
      "attribute" = "jujutsu";
      "declaration" = "nix:nixpkgs:jujutsu";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "package" = {
      "description" = "Jujutsu version-control system (jj)";
      "label" = "Jujutsu";
      "name" = "jj";
      "order" = 30;
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "jj";
      application = (import ./_feature.nix).metadata.application;
    });
}
