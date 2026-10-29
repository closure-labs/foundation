{
  id = "hosts/os/bluefin";
  metadata = {
    ownership = "Bluefin-owned default provisioning and user environment";
  };
  dependencies = [
    "providers/nixpkgs"
  ];
  schemaDependencies = { };
  configuration = schema: import ./_home.nix;
}
