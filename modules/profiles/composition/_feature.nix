{
  "id" = "profiles/composition";
  "metadata" = { };
  "dependencies" = [ ];
  "schemaDependencies" = { };
  configuration = schema: if schema == 3 then import ./_home.nix else { };
}
