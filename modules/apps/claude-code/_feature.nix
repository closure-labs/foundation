import ../../profiles/composition/_nix-application-feature.nix {
  name = "claude-code";
  input = "ai";
  pin = "claude-code";
  attribute = "default";
  package = {label = "Claude Code"; description = "Anthropic command-line coding agent"; order = 120;};
}
