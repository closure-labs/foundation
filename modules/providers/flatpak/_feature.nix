{
  "id" = "providers/flatpak";
  "metadata" = { };
  "dependencies" = [ ];
  "schemaDependencies" = { };
  configuration = schema: { inputs, ... }: {
    imports = [
      inputs.nix-flatpak.homeManagerModules.nix-flatpak
      ./_observations.nix
    ];
  };
}
