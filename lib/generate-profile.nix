# Pure generation boundary: JSON is data, never interpolated Nix code.
{
  profileFile,
  hostFile,
}: let
  catalog = import ./catalog.nix;
  hosts = import ./hosts.nix;
  submitted = builtins.fromJSON (builtins.readFile profileFile);
  overrides = builtins.fromJSON (builtins.readFile hostFile);
  base =
    if submitted ? hardware
    then hosts.fromHardware submitted.hardware
    else {};
  profile = (import ./normalize-profile.nix {inherit catalog;}) (submitted // {host = base // overrides;});
in {
  inherit profile;
  hardware = builtins.mapAttrs (_: entry: {inherit (entry) imageHardware;}) catalog.hardwareByName;
}
