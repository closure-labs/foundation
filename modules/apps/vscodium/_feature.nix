{
  "id" = "apps/vscodium";
  "metadata" = {
    "application" = {
      "attribute" = "vscodium";
      "declaration" = "nix:nixpkgs:vscodium";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "vscodium";
      "declaration" = "nix:nixpkgs:vscodium";
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
        id = "vscodium";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
