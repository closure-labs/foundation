{
  config,
  foundationPackageSets,
  lib,
  pkgs,
  ...
}: let
  chromium = config.lib.nixGL.wrap foundationPackageSets.browser-unstable.ungoogled-chromium;
  profileDirectory = config.xdg.configHome + "/ungoogled-chromium";
  launcher = pkgs.writeShellApplication {
    name = "ungoogled-chromium";
    text = ''
      exec ${lib.getExe' chromium "chromium"} --user-data-dir=${lib.escapeShellArg profileDirectory} "$@"
    '';
  };
in {
  home.packages = [launcher];
  xdg.desktopEntries.ungoogled-chromium = {
    name = "Ungoogled Chromium";
    exec = "${lib.getExe launcher} %U";
    icon = "${chromium}/share/icons/hicolor/128x128/apps/chromium.png";
    categories = ["Network" "WebBrowser"];
    mimeType = ["text/html" "x-scheme-handler/http" "x-scheme-handler/https"];
  };
}
