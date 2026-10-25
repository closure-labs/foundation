{
  "id" = "capabilities/development";
  "metadata" = {
    "capability" = {
      "label" = "Development tools";
      "order" = 120;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = {
    "3" = [
      "apps/devenv"
      "apps/rustup"
      "apps/cargo-audit"
      "apps/cargo-edit"
      "apps/cargo-watch"
      "apps/vscodium"
    ];
  };
}
