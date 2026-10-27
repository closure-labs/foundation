# Ordered roots shared by home construction and the CI graph.
profile:
let
  catalog = import ../../../lib/catalog.nix;
  p = (import ../../../lib/normalize-profile.nix { inherit catalog; }) profile;
  contract = import ../../../lib/profile-drafts/contract.nix { inherit catalog; };
  selected = [
    "profiles/composition"
  ]
  ++ map (name: "capabilities/${name}") contract.commonCapabilities
  ++ map (name: "roles/${name}") p.roles
  ++ map (name: "capabilities/${name}") p.capabilities
  ++ (if p.host.camera then [ "capabilities/camera-controls" ] else [ ])
  ++ map (name: "apps/${name}") p.packages
  ++ [
    "hosts/identity"
    "hosts/machines/${p.host.formFactor}"
    "hosts/cpu/${p.host.cpu}"
    "hosts/models/${p.host.model}"
  ]
  ++ map (name: "hosts/gpu/${name}") p.host.gpus;
in
{
  schema = p.schema;
  roots = [
    "home/base"
  ]
  ++ (
    if
      builtins.elem p.foundation [
        "bluefin"
        "bluefin-dx"
      ]
    then
      [ "hosts/os/bluefin" ]
    else
      [ ]
  )
  ++ selected;
}
