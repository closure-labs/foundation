{
  "id" = "apps/opentofu";
  "metadata" = {
    "application" = {
      "attribute" = "opentofu";
      "declaration" = "nix:nixpkgs:opentofu";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "opentofu";
      "declaration" = "nix:nixpkgs:opentofu";
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
        id = "opentofu";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
