{
  "id" = "apps/uv";
  "metadata" = {
    "application" = {
      "attribute" = "uv";
      "declaration" = "nix:nixpkgs:uv";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "package" = {
      "description" = "Python package and project manager";
      "label" = "uv";
      "name" = "uv";
      "order" = 50;
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "uv";
      application = (import ./_feature.nix).metadata.application;
    });
}
