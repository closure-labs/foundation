import ../../profiles/composition/_nix-application-feature.nix {
  name = "element";
  input = "nixpkgs-weekly";
  pin = "office-weekly";
  attribute = "element-desktop";
  graphical = true;
}
