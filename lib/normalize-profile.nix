# Pure schema-2 validation shared by direct consumers and staged builds.
{catalog}: profile: let
  fail = message: throw "Invalid Foundation profile: ${message}";
  identity = profile.identity or null;
  validSelection = choices: selected:
    builtins.isList selected
    && builtins.all (name: builtins.isString name && builtins.hasAttr name choices) selected
    && builtins.length selected == builtins.length (builtins.attrNames (builtins.listToAttrs (map (name: {
      inherit name;
      value = null;
    }) selected)));
  canonical = choices:
    builtins.sort (a: b:
      if choices.${a}.order == choices.${b}.order
      then a < b
      else choices.${a}.order < choices.${b}.order);
in
  if !builtins.isAttrs profile
  then fail "expected an object"
  else if !builtins.isInt (profile.schema or null) || profile.schema != 2
  then fail "unsupported schema; expected schema 2"
  else if !validSelection catalog.rolesByName (profile.roles or null)
  then fail "invalid or duplicate roles"
  else if !validSelection catalog.packagesByName (profile.packages or null)
  then fail "invalid or duplicate packages"
  else if !builtins.elem (profile.foundation or null) catalog.foundationNames
  then fail "unsupported foundation"
  else if !builtins.elem (profile.hardware or null) catalog.homeHardwareNames
  then fail "unsupported hardware"
  else if
    !builtins.isAttrs identity
    || !builtins.isString (identity.username or null)
    || builtins.match "[a-z_][a-z0-9_-]*[$]?" identity.username == null
    || !builtins.isString (identity.homeDirectory or null)
    || builtins.match "/.+" identity.homeDirectory == null
  then fail "invalid account identity"
  else
    profile
    // {
      roles = canonical catalog.rolesByName profile.roles;
      packages = canonical catalog.packagesByName profile.packages;
    }
