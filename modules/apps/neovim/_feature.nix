{
  "id" = "apps/neovim";
  "metadata" = {
    "application" = {
      "attribute" = "neovim";
      "declaration" = "nix:nixpkgs:neovim";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "neovim";
      application = (import ./_feature.nix).metadata.application;
    });
}
