{
  "id" = "apps/openbao";
  "metadata" = {
    "application" = {
      "attribute" = "openbao";
      "declaration" = "nix:nixpkgs:openbao";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "openbao";
      "declaration" = "nix:nixpkgs:openbao";
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
        id = "openbao";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
