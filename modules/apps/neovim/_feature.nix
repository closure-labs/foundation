{
  "id" = "apps/neovim";
  "metadata" = {
    legacyBaseOrder = 1;
    "application" = {
      "attribute" = "neovim";
      "declaration" = "nix:nixpkgs:neovim";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "neovim";
      "declaration" = "nix:nixpkgs:neovim";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "neovim";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
