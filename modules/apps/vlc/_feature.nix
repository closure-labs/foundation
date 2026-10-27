{
  "id" = "apps/vlc";
  "metadata" = {
    "application" = {
      "attribute" = "vlc";
      "declaration" = "nix:nixpkgs:vlc";
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
      id = "vlc";
      application = (import ./_feature.nix).metadata.application;
    });
}
