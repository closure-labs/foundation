{
  "id" = "apps/marp";
  "metadata" = {
    "application" = {
      "attribute" = "marp-cli";
      "declaration" = "nix:nixpkgs:marp-cli";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "marp";
      application = (import ./_feature.nix).metadata.application;
    });
}
