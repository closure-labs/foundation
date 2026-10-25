{
  "id" = "apps/element";
  "metadata" = {
    legacyBaseOrder = 3;
    "application" = {
      "attribute" = "element-desktop";
      "declaration" = "nix:nixpkgs-weekly:element-desktop";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "element-desktop";
      "declaration" = "nix:nixpkgs-weekly:element-desktop";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
  };
  "dependencies" = [
    "providers/nixpkgs-weekly"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "element";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
