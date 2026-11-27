import ../../profiles/composition/_nix-application-feature.nix {
  name = "lazygit";
  input = "nixpkgs-unstable";
  attribute = "lazygit";
  package = {label = "LazyGit"; description = "Terminal user interface for Git"; order = 130;};
}
