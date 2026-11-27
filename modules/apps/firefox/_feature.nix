{
  "id" = "apps/firefox";
  "metadata" = {
    "application" = {
      "attribute" = "firefox";
      "declaration" = "nix:nixpkgs-unstable:firefox";
      "graphical" = true;
      "input" = "nixpkgs-unstable";
      "pin" = "browser-unstable";
      "provider" = "nix";
      "recipe" = "configured-firefox";
    };
  };
  "dependencies" = [
    "providers/nixpkgs-unstable"
    "providers/graphics"
  ];
  "schemaDependencies" = { };
  configuration = schema: import ./_home.nix;
}
