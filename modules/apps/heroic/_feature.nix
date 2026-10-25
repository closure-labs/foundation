{
  "id" = "apps/heroic";
  "metadata" = {
    "application" = {
      "attribute" = "heroic";
      "declaration" = "nix:nixpkgs:heroic";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "heroic";
      "declaration" = "nix:nixpkgs:heroic";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [
    "providers/nixpkgs"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "heroic";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
