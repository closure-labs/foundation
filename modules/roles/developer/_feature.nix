{
  "id" = "roles/developer";
  "metadata" = {
    "role" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "Developer";
      "name" = "developer";
      "order" = 10;
    };
    "legacyRole" = {
      "classification" = "professional";
      "homeCompatible" = false;
      "label" = "Developer";
      "name" = "developer";
      "order" = 10;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "2" = [
      "capabilities/devops"
      "apps/devenv"
      "apps/rustup"
      "apps/cargo-audit"
      "apps/cargo-edit"
      "apps/cargo-watch"
      "apps/vscodium"
    ];
    "3" = [
      "capabilities/devops"
      "capabilities/development"
    ];
  };
  configuration = schema: if schema == 2 then import ./_home.nix else { };
}
