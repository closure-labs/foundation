import ../../profiles/composition/_nix-application-feature.nix {
  name = "claude-desktop";
  input = "ai";
  pin = "claude-desktop";
  attribute = "default";
  graphical = true;
  package = {label = "Claude Desktop"; description = "Claude desktop client for Linux"; order = 100;};
}
