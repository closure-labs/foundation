# Shared schema-3 composition contract.
{
  catalog,
  applicationContract ? import ../../../lib/profile-drafts/contract.nix {inherit catalog;},
}: let
  contract = applicationContract;
  hosts = import ../../../lib/hosts.nix;
  verification = builtins.fromJSON (builtins.readFile ../../../lib/profile-drafts/flathub-verification.json);
  fail = message: throw "Invalid Foundation profile: ${message}";
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
  normalize = profile:
    if !builtins.isAttrs profile
    then fail "expected an object"
    else if !builtins.isInt (profile.schema or null) || profile.schema != 3
    then fail "unsupported profile schema; expected schema 3. Back up profile.json and recreate it with foundation home profile before updating or applying."
    else let
      host = hosts.normalize (profile.host or (hosts.fromHardware (profile.hardware or "generic-x86_64")));
      hardware = hosts.hardwareFor host;
      identity = profile.identity or null;
      requested = profile.capabilities or [];
    in
      if !selection contract.roles (profile.roles or null)
      then fail "invalid or duplicate roles"
      else if !selection catalog.packagesByName (profile.packages or null)
      then fail "invalid or duplicate packages"
      else if !builtins.elem (profile.foundation or null) catalog.foundationNames
      then fail "unsupported foundation"
      else if !builtins.elem hardware catalog.homeHardwareNames
      then fail "unsupported hardware"
      else if
        !builtins.isAttrs identity
        || !builtins.isString (identity.username or null)
        || builtins.match "[a-z_][a-z0-9_-]*[$]?" identity.username == null
        || !builtins.isString (identity.homeDirectory or null)
        || builtins.match "/.+" identity.homeDirectory == null
      then fail "invalid account identity"
      else if profile ? host && profile ? hardware && profile.hardware != hardware
      then fail "host contradicts the derived hardware adapter; omit hardware or use ${hardware}"
      else if !selection contract.capabilities requested
      then fail "invalid or duplicate capabilities"
      else
        profile
        // {
          inherit host hardware;
          roles = ordered contract.roles profile.roles;
          packages = ordered catalog.packagesByName profile.packages;
          capabilities = ordered contract.capabilities requested;
        };
  declarationsFor = applications: ids:
    builtins.sort builtins.lessThan (map (id: applications.${id}.declaration) ids);
  resolve = profile: let
    normalized = normalize profile;
    effectiveCapabilities = ordered contract.capabilities (unique (
      contract.commonCapabilities
      ++ (
        if normalized.host.camera
        then ["camera-controls"]
        else []
      )
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
in {
  inherit contract verification normalize resolve;
  status = "draft";
  activationAllowed = false;
}
