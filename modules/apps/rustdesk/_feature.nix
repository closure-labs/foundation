{
  "id" = "apps/rustdesk";
  "metadata" = {
    "application" = {
      "attribute" = "rustdesk-flutter";
      "declaration" = "nix:nixpkgs:rustdesk-flutter";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "rustdesk-flutter";
      "declaration" = "nix:nixpkgs:rustdesk-flutter";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
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
        id = "rustdesk";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
