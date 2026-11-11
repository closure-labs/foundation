{
  "id" = "apps/smile";
  "metadata" = {
    "application" = {
      "attribute" = "smile";
      "declaration" = "nix:nixpkgs:smile";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "removeIconBuildFiles" = true;
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
      id = "smile";
      application = (import ./_feature.nix).metadata.application;
    });
}
