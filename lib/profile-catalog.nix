# One current projection for the library, packaged tools and profile generator.
{
  domainCatalog,
  lib,
  version,
  schema ? 3,
}: let
  contract = import ./profile-drafts/contract.nix {catalog = domainCatalog;};
  roles = domainCatalog.rolesByName // contract.roles;
  selected =
    domainCatalog
    // {
      rolesByName = roles;
      roleNames = builtins.sort (a: b:
        if roles.${a}.order == roles.${b}.order
        then a < b
        else roles.${a}.order < roles.${b}.order)
      (builtins.attrNames roles);
    };
  project = domainCatalog: import ./home-catalog.nix {inherit domainCatalog lib version;};
in
  if schema == 2
  then (project domainCatalog) // {profileSchema = 2;}
  else if schema == 3
  then
    (project selected)
    // {
      profileSchema = 3;
      capabilities = contract.capabilities;
      hosts = (import ./hosts.nix).choices;
    }
  else throw "Unsupported Foundation catalog profile schema"
