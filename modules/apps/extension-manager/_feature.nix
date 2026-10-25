{
  "id" = "apps/extension-manager";
  "metadata" = {
    "application" = {
      "attribute" = "gnome-extension-manager";
      "declaration" = "nix:nixpkgs:gnome-extension-manager";
      "graphical" = true;
      "input" = "nixpkgs";
      "provider" = "nix";
    };
    "legacyApplication" = {
      "declaration" = "flatpak:flathub:com.mattjakeman.ExtensionManager";
      "graphical" = true;
      "id" = "com.mattjakeman.ExtensionManager";
      "provider" = "flatpak";
      "remote" = "flathub";
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ "providers/flatpak" ];
    "3" = [
      "providers/nixpkgs"
      "providers/graphics"
    ];
  };
  configuration =
    schema:
    if schema == 3 then
      (import ../../profiles/composition/_application.nix {
        id = "extension-manager";
        application = (import ./_feature.nix).metadata.application;
      })
    else
      { };
}
