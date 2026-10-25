{
  "id" = "roles/support";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Support";
      "name" = "support";
      "order" = 40;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Support";
      "name" = "support";
      "order" = 40;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [
      "capabilities/devops"
      "apps/espanso"
      "apps/rustconn"
    ];
    "3" = [
      "capabilities/devops"
      "capabilities/support-tools"
    ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
