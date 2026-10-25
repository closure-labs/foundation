{
  "id" = "apps/packer";
  "metadata" = {
    "application" = {
      "attribute" = "packer";
      "declaration" = "nix:nixpkgs:packer";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "packer";
      "declaration" = "nix:nixpkgs:packer";
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
        id = "packer";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
