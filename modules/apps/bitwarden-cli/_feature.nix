{
  "id" = "apps/bitwarden-cli";
  "metadata" = {
    legacyBaseOrder = 8;
    "application" = {
      "attribute" = "bitwarden-cli";
      "declaration" = "nix:nixpkgs-weekly:bitwarden-cli";
      "graphical" = false;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "bitwarden-cli";
      "declaration" = "nix:nixpkgs-weekly:bitwarden-cli";
      "graphical" = false;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs-weekly" ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "bitwarden-cli";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
