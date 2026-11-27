import ../../profiles/composition/_nix-application-feature.nix {
  name = "1password";
  input = "nixpkgs";
  attribute = "_1password-gui";
  graphical = true;
  package = {label = "1Password"; description = "Desktop password manager"; order = 60;};
}
