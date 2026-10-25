{
  "id" = "home/legacy";
  "metadata" = { };
  "dependencies" = [ "profiles/composition" ];
  "schemaDependencies" = {
    "2" = [
      "apps/firefox"
      "apps/neovim"
      "apps/marp"
      "apps/bitwarden"
      "apps/bitwarden-cli"
      "apps/element"
      "apps/libreoffice"
      "apps/nextcloud"
      "apps/thunderbird"
      "apps/vlc"
      "apps/damask"
      "apps/gradia"
      "apps/pinta"
      "apps/flatseal"
      "apps/extension-manager"
      "apps/distroshelf"
      "apps/camera-controls"
      "apps/ignition"
      "apps/warehouse"
      "apps/icebox"
      "apps/spider"
      "apps/impression"
      "apps/mission-center"
      "apps/gearlever"
      "apps/smile"
      "apps/joplin"
      "apps/chromium"
      "apps/refine"
    ];
  };
  configuration = schema: import ./_home.nix;
}
