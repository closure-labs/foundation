{
  "id" = "apps/nextcloud";
  "metadata" = {
    legacyBaseOrder = 5;
    "application" = {
      "attribute" = "nextcloud-client";
      "declaration" = "nix:nixpkgs-weekly:nextcloud-client";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "nextcloud-client";
      "declaration" = "nix:nixpkgs-weekly:nextcloud-client";
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
        id = "nextcloud";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
