{
  "id" = "apps/bitwarden-cli";
  "metadata" = {
    "application" = {
      "attribute" = "bitwarden-cli";
      "declaration" = "nix:nixpkgs-weekly:bitwarden-cli";
      "graphical" = false;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs-weekly" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "bitwarden-cli";
      application = (import ./_feature.nix).metadata.application;
    });
}
