{
  "id" = "capabilities/devops";
  "metadata" = {
    "capability" = {
      "label" = "Development operations";
      "order" = 110;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "3" = [
      "apps/ghostty"
      "apps/ansible"
      "apps/openbao"
      "apps/opentofu"
      "apps/packer"
      "apps/distroshelf"
    ];
  };
  configuration = schema: import ./_home.nix;
}
