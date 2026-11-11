{
  "id" = "apps/extension-manager";
  "metadata" = {
    "application" = {
      "attribute" = "gnome-extension-manager";
      "declaration" = "nix:nixpkgs:gnome-extension-manager";
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
      id = "extension-manager";
      application = (import ./_feature.nix).metadata.application;
    });
}
