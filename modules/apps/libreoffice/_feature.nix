{
  "id" = "apps/libreoffice";
  "metadata" = {
    legacyBaseOrder = 4;
    "application" = {
      "attribute" = "libreoffice";
      "declaration" = "nix:nixpkgs-weekly:libreoffice";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "libreoffice";
      "declaration" = "nix:nixpkgs-weekly:libreoffice";
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
        id = "libreoffice";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
