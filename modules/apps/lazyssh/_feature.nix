import ../../profiles/composition/_nix-application-feature.nix {
  name = "lazyssh";
  input = "nixpkgs-unstable";
  attribute = "lazyssh";
  package = {label = "LazySSH"; description = "Terminal SSH connection manager"; order = 140;};
}
