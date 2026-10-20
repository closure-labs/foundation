# Executable design contract only. This is intentionally outside normalizeProfile.
{
  catalog,
  applicationContract ? import ./contract.nix {inherit catalog;},
}: let
  contract = applicationContract;
  verification = builtins.fromJSON (builtins.readFile ./flathub-verification.json);
  fail = message: throw "Invalid draft Foundation profile: ${message}";
  unique = values:
    builtins.attrNames (builtins.listToAttrs (map (name: {
        inherit name;
        value = null;
      })
      values));
  ordered = choices:
    builtins.sort (a: b:
      if choices.${a}.order == choices.${b}.order
      then a < b
      else choices.${a}.order < choices.${b}.order);
  selection = choices: values:
    builtins.isList values
    && builtins.all (name: builtins.isString name && builtins.hasAttr name choices) values
    && builtins.length values == builtins.length (unique values);
  concatMap = f: values: builtins.concatLists (map f values);
  legacyNormalize = import ../normalize-profile.nix {inherit catalog;};
  draftBaseNormalize = import ../normalize-profile.nix {
    catalog =
      catalog
      // {
        rolesByName = contract.roles;
        roleNames = ordered contract.roles (builtins.attrNames contract.roles);
      };
  };
  normalize = profile:
    if !builtins.isAttrs profile || !builtins.isInt (profile.schema or null) || profile.schema != 3
    then fail "expected schema 3"
    else let
      checked = draftBaseNormalize (profile // {schema = 2;});
      requested = profile.capabilities or [];
    in
      if !selection contract.capabilities requested
      then fail "invalid or duplicate capabilities"
      else
        checked
        // {
          schema = 3;
          capabilities = ordered contract.capabilities requested;
        };
  declarationsFor = applications: ids:
    builtins.sort builtins.lessThan (map (id: applications.${id}.declaration) ids);
  resolve = profile: let
    normalized = normalize profile;
    effectiveCapabilities = ordered contract.capabilities (unique (
      contract.commonCapabilities
      ++ contract.hardwareCapabilities.${normalized.hardware}
      ++ concatMap (name: contract.roles.${name}.capabilities) normalized.roles
      ++ normalized.capabilities
    ));
    applicationIds = unique (
      concatMap (name: contract.capabilities.${name}.applications) effectiveCapabilities
      ++ map (name: contract.optionalPackages.${name}) normalized.packages
    );
    selectedFlatpaks = builtins.filter (id: contract.applications.${id}.provider == "flatpak") applicationIds;
    allowed = builtins.all (id: let
      app = contract.applications.${id};
      evidence = verification.applications.${app.id} or {};
    in
      (evidence.verified or false) == true)
    selectedFlatpaks;
  in
    if !allowed
    then fail "Flatpak provider lacks recorded publisher verification"
    else {
      profile = normalized;
      inherit applicationIds effectiveCapabilities;
      classifications = builtins.filter (classification:
        builtins.any (name: contract.roles.${name}.classification == classification) normalized.roles)
      catalog.classificationNames;
      applications = builtins.listToAttrs (map (name: {
          inherit name;
          value = contract.applications.${name};
        })
        applicationIds);
      declarations = declarationsFor contract.applications applicationIds;
      wrappedApplicationIds = builtins.filter (name:
        contract.applications.${name}.provider == "nix" && contract.applications.${name}.graphical)
      applicationIds;
      inherit (contract) graphics infrastructure;
    };
  resolveLegacy = profile: let
    normalized = legacyNormalize profile;
    applicationIds = unique (
      contract.legacy.commonApplications
      ++ concatMap (name: contract.legacy.roleApplications.${name}) normalized.roles
      ++ map (name: contract.optionalPackages.${name}) normalized.packages
    );
  in {
    profile = normalized;
    inherit applicationIds;
    declarations = declarationsFor contract.legacyApplications applicationIds;
  };
  difference = left: right: builtins.filter (value: !builtins.elem value right) left;
in {
  inherit contract verification normalize resolve resolveLegacy;
  status = "draft";
  activationAllowed = false;
  previewMigration = {
    profile,
    roles ? null,
    capabilities ? [],
  }: let
    old = resolveLegacy profile;
    collision = builtins.hasAttr "capabilities" old.profile;
    candidate =
      old.profile
      // {
        schema = 3;
        inherit capabilities;
        roles =
          if roles == null
          then old.profile.roles
          else roles;
      };
    next = resolve candidate;
    common = builtins.filter (id: builtins.elem id next.applicationIds) old.applicationIds;
    removedDeclarations = difference old.declarations next.declarations;
    providerChanges = map (id: {
      application = id;
      before = contract.legacyApplications.${id}.declaration;
      after = contract.applications.${id}.declaration;
    }) (builtins.filter (id: contract.legacyApplications.${id}.declaration != contract.applications.${id}.declaration) common);
  in
    if collision
    then {
      status = "blocked";
      activationAllowed = false;
      reason = "Existing custom capabilities field collides with schema 3; resolve it explicitly before migration";
      source = old.profile;
      candidate = null;
    }
    else {
      status = "preview";
      activationAllowed = false;
      source = old.profile;
      candidate = next.profile;
      inherit (next) classifications effectiveCapabilities;
      changes = {
        addedApplications = difference next.applicationIds old.applicationIds;
        removedApplications = difference old.applicationIds next.applicationIds;
        addedDeclarations = difference next.declarations old.declarations;
        inherit removedDeclarations;
        retainedDeclarations = builtins.filter (declaration: builtins.elem declaration next.declarations) old.declarations;
        inherit providerChanges;
        graphics = {
          before = contract.graphics.legacyBackend;
          after = contract.graphics.preferredBackend;
        };
      };
      flatpak = {
        uninstallUnmanaged = false;
        deleteApplicationData = false;
        removedDeclarationsMayRemainInstalled = builtins.filter (declaration: builtins.substring 0 8 declaration == "flatpak:") removedDeclarations;
        migrateApplicationDataAutomatically = false;
      };
      requirements = {
        readerSchema = 3;
        explicitMigration = true;
        approveProviderChanges = providerChanges != [];
        graphicsSessionValidation = true;
      };
    };
}
