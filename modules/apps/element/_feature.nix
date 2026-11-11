import ../../profiles/composition/_nix-application-feature.nix {
  name = "element";
  input = "nixpkgs-weekly";
  attribute = "element-desktop";
  graphical = true;
}
