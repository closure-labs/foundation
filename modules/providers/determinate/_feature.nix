{
  "id" = "providers/determinate";
  "metadata" = { };
  "dependencies" = [ ];
  "schemaDependencies" = { };
  configuration = schema: { inputs, ... }: {
    imports = [ inputs.determinate.homeManagerModules.default ];
  };
}
