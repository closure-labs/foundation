# Pure discovery: no flake, Nixpkgs or configuration evaluation required.
{ root ? ../.. }:
let
  walk = relative: let
    directory = root + (if relative == "" then "" else "/${relative}");
    entries = builtins.readDir directory;
    here = if entries ? "_feature.nix" then [ { id = relative; path = directory + "/_feature.nix"; } ] else [];
  in here ++ builtins.concatLists (map (name:
    if entries.${name} == "directory" && builtins.substring 0 1 name != "_"
    then walk (if relative == "" then name else "${relative}/${name}") else []) (builtins.attrNames entries));
  discovered = walk "";
  features = builtins.listToAttrs (map (entry: {
    name = entry.id;
    value = let descriptor = import entry.path; in
      if descriptor.id != entry.id then throw "Feature ID must match path: ${entry.id}" else descriptor;
  }) discovered);
  dependencies = schema: id:
    if schema != 3 then throw "Unsupported Foundation profile schema; expected schema 3. Recreate the profile with foundation home profile."
    else features.${id}.dependencies ++ (features.${id}.schemaDependencies.${toString schema} or []);
  visit = schema: trail: id:
    if !(builtins.hasAttr id features) then throw "Missing feature dependency: ${id}"
    else if builtins.elem id trail then throw "Feature dependency cycle: ${builtins.concatStringsSep " -> " (trail ++ [id])}"
    else [id] ++ builtins.concatLists (map (visit schema (trail ++ [id])) (dependencies schema id));
  unique = values: builtins.foldl' (acc: value: if builtins.elem value acc then acc else acc ++ [value]) [] values;
  closure = schema: roots:
    if schema != 3 then throw "Unsupported Foundation profile schema; expected schema 3. Recreate the profile with foundation home profile."
    else unique (builtins.concatLists (map (visit schema []) roots));
  validated = builtins.deepSeq (map (schema: closure schema (builtins.attrNames features)) [3]) features;
in { features = validated; inherit dependencies closure; }
