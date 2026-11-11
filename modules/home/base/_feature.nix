{
  "id" = "home/base";
  "metadata" = {
    "commonCapabilities" = [
      "essentials"
      "desktop-tools"
    ];
    "infrastructure" = [
      "Foundation commands and transactional activation"
      "Managed Git/nh/Zsh integration"
      "Fonts and XDG paths"
      "Generic Linux integration"
      "Role flags and existing role-specific configuration"
      "Dell panel and IPU7/Firefox camera configuration"
    ];
    "graphics" = {
      "globalLibraryExports" = false;
      "offload" = "explicit-only";
      "preferredBackend" = "nixgl-mesa";
      "vulkanDefault" = false;
      "wrapper" = "config.lib.nixGL.wrap";
    };
  };
  "dependencies" = [
    "profiles/catalog"
    "profiles/schema"
    "profiles/generation"
    "profiles/editing"
    "home/construction"
    "providers/determinate"
    "providers/flatpak"
    "apps/firefox"
    "providers/graphics"
    "home/shell"
    "home/activation"
    "home/commands"
    "home/password-managers"
  ];
  "schemaDependencies" = { };
  configuration = schema: import ./_home.nix;
}
