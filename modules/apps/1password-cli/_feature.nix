import ../../profiles/composition/_nix-application-feature.nix {
  name = "1password-cli";
  input = "nixpkgs";
  pin = "passwords-stable";
  attribute = "_1password-cli";
  package = {label = "1Password CLI"; description = "Command-line password manager"; order = 70;};
}
