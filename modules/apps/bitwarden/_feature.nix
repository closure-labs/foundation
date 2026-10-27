{
  "id" = "apps/bitwarden";
  "metadata" = {
    "application" = {
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
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "bitwarden";
      application = (import ./_feature.nix).metadata.application;
    });
}
