{
  "id" = "apps/kdenlive";
  "metadata" = {
    "application" = {
      "attribute" = "kdePackages.kdenlive";
      "declaration" = "nix:nixpkgs:kdePackages.kdenlive";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "kdePackages.kdenlive";
      "declaration" = "nix:nixpkgs:kdePackages.kdenlive";
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
        id = "kdenlive";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
