{
  "id" = "apps/ansible";
  "metadata" = {
    "application" = {
      "attribute" = "ansible";
      "declaration" = "nix:nixpkgs:ansible";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "ansible";
      application = (import ./_feature.nix).metadata.application;
    });
}
