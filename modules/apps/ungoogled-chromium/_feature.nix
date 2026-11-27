(import ../../profiles/composition/_nix-application-feature.nix {
  name = "ungoogled-chromium";
  input = "nixpkgs-unstable";
  graphical = true;
  attribute = "ungoogled-chromium";
  package = {label = "Ungoogled Chromium"; description = "Chromium with Google service integration removed"; order = 150;};
}) // {
  configuration = _: import ./_home.nix;
}
