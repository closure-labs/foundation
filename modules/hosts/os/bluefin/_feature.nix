{
  id = "hosts/os/bluefin";
  metadata = {
    ownership = "Inherited Bluefin CLI bundle and user environment";
  };
  dependencies = [
    "providers/nixpkgs"
    "providers/nixpkgs-unstable"
  ];
  schemaDependencies = { };
  configuration = schema: import ./_home.nix;
}
