{
  "id" = "roles/it";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "IT";
      "name" = "it";
      "order" = 60;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "IT";
      "name" = "it";
      "order" = 60;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [ "apps/rustdesk" ];
    "3" = [ "capabilities/remote-desktop" ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
