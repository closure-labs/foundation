{
  "id" = "roles/trainer";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Trainer";
      "name" = "trainer";
      "order" = 30;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = true;
      "label" = "Trainer";
      "name" = "trainer";
      "order" = 30;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ "apps/grist" ];
    "3" = [
      "capabilities/office"
      "capabilities/presentations"
      "capabilities/image-editing"
      "capabilities/trainer-links"
    ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
