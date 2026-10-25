{
  "id" = "apps/espanso";
  "metadata" = {
    "application" = {
      "attribute" = "espanso-wayland";
      "declaration" = "nix:nixpkgs:espanso-wayland";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "attribute" = "espanso-wayland";
      "declaration" = "nix:nixpkgs:espanso-wayland";
      "graphical" = false;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
  };
  "dependencies" = [ "providers/nixpkgs" ];
  "schemaDependencies" = { };
  configuration = schema: {
    imports = [
      ./_settings.nix
    ]
    ++ (
      if schema == 3 then
        [
          (import ../../profiles/composition/_application.nix {
            id = "espanso";
            application = (import ./_feature.nix).metadata.application;
          })
        ]
      else
        [ ]
    );
  };
}
