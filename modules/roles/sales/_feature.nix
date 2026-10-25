{
  "id" = "roles/sales";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Sales";
      "name" = "sales";
      "order" = 20;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Sales";
      "name" = "sales";
      "order" = 20;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ ];
    "3" = [
      "capabilities/office"
      "capabilities/mail"
    ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
