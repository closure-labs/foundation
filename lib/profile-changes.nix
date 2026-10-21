# Pure selection and migration preview. This never authorizes activation.
{catalog}: {
  profile,
  roles ? null,
  packages ? null,
  capabilities ? null,
  migrate ? false,
}: let
  composition = import ./profile-drafts {inherit catalog;};
  fail = message: throw "Invalid Foundation profile change: ${message}";
  resolve = value:
    if value.schema == 2
    then composition.resolveLegacy value
    else composition.resolve value;
  old = resolve profile;
  source = old.profile;
  collision = migrate && builtins.hasAttr "capabilities" source;
  candidate =
    source
    // {
      schema =
        if migrate
        then 3
        else source.schema;
    }
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
      else if migrate
      then {capabilities = [];}
      else {}
    );
  next = resolve candidate;
  difference = left: right: builtins.filter (value: !builtins.elem value right) left;
  applications = value:
    if value.profile.schema == 2
    then composition.contract.legacyApplications
    else composition.contract.applications;
  common = builtins.filter (id: builtins.elem id next.applicationIds) old.applicationIds;
  removedDeclarations = difference old.declarations next.declarations;
  providerChanges = map (id: {
    application = id;
    before = (applications old).${id}.declaration;
    after = (applications next).${id}.declaration;
  }) (builtins.filter (id: (applications old).${id}.declaration != (applications next).${id}.declaration) common);
  graphics = value:
    if value.profile.schema == 2
    then composition.contract.graphics.legacyBackend
    else composition.contract.graphics.preferredBackend;
in
  if !builtins.isAttrs profile || !(builtins.elem (profile.schema or null) [2 3])
  then fail "expected schema 2 or 3"
  else if migrate && source.schema != 2
  then fail "conversion requires a schema-2 source"
  else if !migrate && source.schema == 2 && capabilities != null
  then fail "capabilities require explicit conversion to schema 3"
  else if collision
  then {
    status = "blocked";
    activationAllowed = false;
    reason = "Existing custom capabilities field collides with schema 3; resolve it explicitly before migration";
    inherit source;
    candidate = null;
  }
  else {
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
