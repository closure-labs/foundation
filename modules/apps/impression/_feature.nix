{
  "id" = "apps/impression";
  "metadata" = {
    "application" = {
      "attribute" = "impression";
      "declaration" = "nix:nixpkgs:impression";
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
      id = "impression";
      application = (import ./_feature.nix).metadata.application;
    });
}
