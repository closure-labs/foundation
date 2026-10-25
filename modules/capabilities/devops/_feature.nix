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
    "2" = [
      "apps/ghostty"
      "apps/ansible"
      "apps/openbao"
      "apps/opentofu"
      "apps/packer"
    ];
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
