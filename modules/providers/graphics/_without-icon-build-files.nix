# These Meson install_subdir leftovers are source files, not runtime icons.
{
  pkgs,
  package,
}:
package.overrideAttrs (old: {
  buildCommand =
    old.buildCommand
    + ''
      if [ -d "$out/share/icons" ]; then
        ${pkgs.findutils}/bin/find "$out/share/icons" -name meson.build -delete
      fi
    '';
})
