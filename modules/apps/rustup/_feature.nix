{
  "id" = "apps/rustup";
  "metadata" = {
    "application" = {
      "attribute" = "rustup";
      "declaration" = "nix:nixpkgs:rustup";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "rustup";
      application = (import ./_feature.nix).metadata.application;
    });
}
