{
  "id" = "apps/firefox";
  "metadata" = {
    "application" = {
      "attribute" = "firefox";
      "declaration" = "nix:nixpkgs-weekly:firefox";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
      "recipe" = "configured-firefox";
    };
    "legacyApplication" = {
      "attribute" = "firefox";
      "declaration" = "nix:nixpkgs-weekly:firefox";
      "graphical" = true;
      "input" = "nixpkgs-weekly";
      "provider" = "nix";
      "recipe" = "configured-firefox";
    };
  };
  "dependencies" = [
    "providers/nixpkgs-weekly"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration = schema: import ./_home.nix;
}
