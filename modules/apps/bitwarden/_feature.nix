import ../../profiles/composition/_nix-application-feature.nix {
  name = "bitwarden";
  input = "nixpkgs-weekly";
  attribute = "bitwarden-desktop";
  graphical = true;
}
