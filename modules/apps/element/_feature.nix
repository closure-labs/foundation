import ../../profiles/composition/_nix-application-feature.nix {
  name = "element";
  input = "nixpkgs-unstable";
  attribute = "element-desktop";
  graphical = true;
}
