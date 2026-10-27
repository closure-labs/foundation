{
  "id" = "apps/joplin";
  "metadata" = {
    "application" = {
      "attribute" = "joplin-desktop";
      "declaration" = "nix:nixpkgs:joplin-desktop";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "3" = [
      "providers/nixpkgs"
      "providers/graphics"
    ];
  };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "joplin";
      application = (import ./_feature.nix).metadata.application;
    });
}
