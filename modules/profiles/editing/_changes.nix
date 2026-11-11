# Pure selection preview. This never authorizes activation.
{catalog}: {
  profile,
  roles ? null,
  packages ? null,
  capabilities ? null,
}: let
  composition = import ../../../lib/profile-drafts {inherit catalog;};
  resolve = composition.resolve;
  old = resolve profile;
  source = old.profile;
  candidate = source
    // (
      if roles == null
      then {}
      else {inherit roles;}
    )
    // (
      if packages == null
      then {}
      else {inherit packages;}
    )
    // (
      if capabilities != null
      then {inherit capabilities;}
      else {}
    );
  next = resolve candidate;
  difference = left: right: builtins.filter (value: !builtins.elem value right) left;
  applications = value: composition.contract.applications;
  common = builtins.filter (id: builtins.elem id next.applicationIds) old.applicationIds;
  removedDeclarations = difference old.declarations next.declarations;
  providerChanges = map (id: {
    application = id;
    before = (applications old).${id}.declaration;
    after = (applications next).${id}.declaration;
  }) (builtins.filter (id: (applications old).${id}.declaration != (applications next).${id}.declaration) common);
  graphics = value: composition.contract.graphics.preferredBackend;
in {
  status = "preview";
  activationAllowed = false;
  inherit source;
  candidate = next.profile;
  effectiveCapabilities = next.effectiveCapabilities or [];
  changes = {
    addedApplications = difference next.applicationIds old.applicationIds;
    removedApplications = difference old.applicationIds next.applicationIds;
    addedDeclarations = difference next.declarations old.declarations;
    inherit removedDeclarations providerChanges;
    retainedDeclarations = builtins.filter (declaration: builtins.elem declaration next.declarations) old.declarations;
    graphics = {
      before = graphics old;
      after = graphics next;
    };
  };
  flatpak = {
    uninstallUnmanaged = false;
    deleteApplicationData = false;
    migrateApplicationDataAutomatically = false;
    removedDeclarationsMayRemainInstalled = builtins.filter (declaration: builtins.substring 0 8 declaration == "flatpak:") removedDeclarations;
  };
}
