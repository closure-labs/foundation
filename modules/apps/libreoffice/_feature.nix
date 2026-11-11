import ../../profiles/composition/_nix-application-feature.nix {
  name = "libreoffice";
  input = "nixpkgs-weekly";
  pin = "office-weekly";
  attribute = "libreoffice";
  graphical = true;
}
