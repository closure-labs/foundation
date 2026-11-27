import ../../profiles/composition/_nix-application-feature.nix {
  name = "zoom";
  input = "nixpkgs-weekly";
  attribute = "zoom-us";
  graphical = true;
  recipe = "zoom-gnome-media-keys";
  package = {label = "Zoom"; description = "Video meetings"; order = 80;};
}
