{
  "id" = "apps/nextcloud";
  "metadata" = {
    "application" = {
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
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "nextcloud";
      application = (import ./_feature.nix).metadata.application;
    });
}
