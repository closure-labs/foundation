{
  "id" = "apps/element";
  "metadata" = {
    "application" = {
      "attribute" = "element-desktop";
      "declaration" = "nix:nixpkgs-weekly:element-desktop";
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
      id = "element";
      application = (import ./_feature.nix).metadata.application;
    });
}
