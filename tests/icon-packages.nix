# Build the actual wrapped pair: an evaluation alone misses buildEnv collisions.
{foundation}: let
  profile =
    (builtins.fromJSON (builtins.readFile ../profile.json))
    // {
      schema = 3;
      roles = [];
      packages = [];
      capabilities = ["desktop-comforts"];
    };
  home = foundation.lib.mkHomeConfiguration {inherit profile;};
  inherit (home) pkgs;
  packages = builtins.filter (p: builtins.elem (p.pname or "") ["gearlever" "smile"]) home.config.home.packages;
  merged = pkgs.buildEnv {
    name = "foundation-desktop-icons";
    paths = packages;
  };
in
  pkgs.runCommand "foundation-desktop-icon-check" {} ''
    test ${toString (builtins.length packages)} -eq 2
    test -x ${merged}/bin/smile
    test -x ${merged}/bin/gearlever
    test -d ${merged}/share/icons/hicolor
    test -f ${merged}/share/icons/hicolor/scalable/apps/it.mijorus.smile.svg
    test -f ${merged}/share/icons/hicolor/scalable/apps/it.mijorus.gearlever.svg
    test -z "$(${pkgs.findutils}/bin/find -L ${merged}/share/icons -name meson.build -print -quit)"
    touch "$out"
  ''
