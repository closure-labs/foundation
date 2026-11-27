import ../../profiles/composition/_nix-application-feature.nix {
  name = "nextcloud";
  input = "nixpkgs-weekly";
  attribute = "nextcloud-client";
  graphical = true;
}
