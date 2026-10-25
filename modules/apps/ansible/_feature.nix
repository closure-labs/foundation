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
    "legacyApplication" = {
      "attribute" = "ansible";
      "declaration" = "nix:nixpkgs:ansible";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "ansible";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
