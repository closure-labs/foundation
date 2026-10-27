{
  "id" = "apps/hack-font";
  "metadata" = {
    "application" = {
      "attribute" = "nerd-fonts.hack";
      "declaration" = "nix:nixpkgs:nerd-fonts.hack";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "package" = {
      "description" = "Hack font patched with Nerd Fonts glyphs";
      "label" = "Hack Nerd Font";
      "name" = "hack-font";
      "order" = 10;
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema:
    (import ../../profiles/composition/_application.nix {
      id = "hack-font";
      application = (import ./_feature.nix).metadata.application;
    });
}
