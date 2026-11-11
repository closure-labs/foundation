# Preserve the existing Ghostty desktop launch policy before nixGL wrapping.
{pkgs}:
pkgs.symlinkJoin {
  name = "finite-ghostty-${pkgs.ghostty.version}";
  paths = [pkgs.ghostty];
  postBuild = ''
    desktop="$out/share/applications/com.mitchellh.ghostty.desktop"
    desktop_source=$(readlink -f "$desktop")
    install -m 0444 "$desktop_source" "$desktop.new"
    substituteInPlace "$desktop.new" \
      --replace-fail 'DBusActivatable=true' 'DBusActivatable=false'
    mv -f "$desktop.new" "$desktop"
  '';
  meta.mainProgram = "ghostty";
}
