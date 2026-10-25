{
  "id" = "apps/bitwarden";
  "metadata" = {
    legacyBaseOrder = 2;
    "application" = {
      "attribute" = "bitwarden-desktop";
      "declaration" = "nix:nixpkgs-weekly:bitwarden-desktop";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "bitwarden-desktop";
      "declaration" = "nix:nixpkgs-weekly:bitwarden-desktop";
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
        id = "bitwarden";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
