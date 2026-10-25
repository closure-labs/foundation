{
  "id" = "roles/executive";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "Executive";
      "name" = "executive";
      "order" = 50;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "Executive";
      "name" = "executive";
      "order" = 50;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ "apps/vates-notes" ];
    "3" = [
      "capabilities/office"
      "capabilities/mail"
      "capabilities/executive-links"
    ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
