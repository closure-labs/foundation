{
  "id" = "apps/libreoffice";
  "metadata" = {
    "application" = {
      "attribute" = "libreoffice";
      "declaration" = "nix:nixpkgs-weekly:libreoffice";
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
      id = "libreoffice";
      application = (import ./_feature.nix).metadata.application;
    });
}
