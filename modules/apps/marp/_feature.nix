{
  "id" = "apps/marp";
  "metadata" = {
    legacyBaseOrder = 0;
    "application" = {
      "attribute" = "marp-cli";
      "declaration" = "nix:nixpkgs:marp-cli";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "marp-cli";
      "declaration" = "nix:nixpkgs:marp-cli";
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
        id = "marp";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
