# Build a synthetic application through the actual pinned HM/nixGL machinery.
{foundation}: let
  profile = (builtins.fromJSON (builtins.readFile ../profile.json)) // {schema = 3;};
  home = foundation.lib.mkHomeConfiguration {inherit profile;};
  pkgs = home.pkgs;
  app = pkgs.runCommand "foundation-wrapper-fixture" {meta.mainProgram = "fixture";} ''
    mkdir -p "$out/bin" "$out/share/applications" "$out/share/dbus-1/services" "$out/share/systemd/user"
    printf '#!${pkgs.runtimeShell}\nprintf "wrapped fixture: %%s\\n" "$1"\n' > "$out/bin/fixture"
    chmod +x "$out/bin/fixture"
    printf '[Desktop Entry]\nType=Application\nName=Fixture\nExec=%s/bin/fixture desktop\n' "$out" > "$out/share/applications/fixture.desktop"
    printf '[D-BUS Service]\nName=org.foundation.Fixture\nExec=%s/bin/fixture dbus\n' "$out" > "$out/share/dbus-1/services/fixture.service"
    printf '[Service]\nExecStart=%s/bin/fixture service\n' "$out" > "$out/share/systemd/user/fixture.service"
  '';
  wrapped = home.config.lib.nixGL.wrap app;
in
  pkgs.runCommand "foundation-nixgl-launch-paths" {} ''
    test "${app}" != "${wrapped}"
    for file in share/applications/fixture.desktop share/dbus-1/services/fixture.service share/systemd/user/fixture.service; do
      grep -F '${wrapped}/bin/fixture' "${wrapped}/$file"
      if grep -F '${app}/bin/fixture' "${wrapped}/$file"; then exit 1; fi
    done
    grep -F nixGLCombinedWrapper '${wrapped}/bin/fixture'
    '${wrapped}/bin/fixture' 'argument with spaces' > result.txt
    grep -Fx 'wrapped fixture: argument with spaces' result.txt
    touch "$out"
  ''
