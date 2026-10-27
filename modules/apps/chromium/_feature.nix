{
  "id" = "apps/chromium";
  "metadata" = {
    "application" = {
      "attribute" = "chromium";
      "declaration" = "nix:nixpkgs:chromium";
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
      id = "chromium";
      application = (import ./_feature.nix).metadata.application;
    });
}
