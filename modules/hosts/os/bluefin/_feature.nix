{
  id = "hosts/os/bluefin";
  metadata = {
    ownership = "Inherited Bluefin CLI bundle and user environment";
  };
  dependencies = [
    "providers/nixpkgs"
  ];
  schemaDependencies = { };
  configuration = schema: import ./_home.nix;
}
