{
  "id" = "apps/ghostty";
  "metadata" = {
    "application" = {
      "attribute" = "ghostty";
      "declaration" = "nix:nixpkgs:ghostty";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "recipe" = "finite-ghostty";
    };
    "legacyApplication" = {
      "attribute" = "ghostty";
      "declaration" = "nix:nixpkgs:ghostty";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
      "recipe" = "finite-ghostty";
    };
  };
  "dependencies" = [
    "providers/nixpkgs"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "ghostty";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
