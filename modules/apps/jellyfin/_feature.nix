{
  "id" = "apps/jellyfin";
  "metadata" = {
    "application" = {
      "attribute" = "jellyfin-desktop";
      "declaration" = "nix:nixpkgs:jellyfin-desktop";
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
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "jellyfin";
      application = (import ./_feature.nix).metadata.application;
    });
}
