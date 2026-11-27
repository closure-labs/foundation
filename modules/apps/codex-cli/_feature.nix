import ../../profiles/composition/_nix-application-feature.nix {
  name = "codex-cli";
  input = "ai";
  pin = "codex-cli-nix";
  attribute = "default";
  package = {label = "Codex CLI"; description = "OpenAI command-line coding agent"; order = 110;};
}
