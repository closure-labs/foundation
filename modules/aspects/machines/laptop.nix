{lib, ...}: {
  home.sessionVariables.FINITE_FORM_FACTOR = "laptop";
  # A user preference, not another power daemon or suspend/lid controller.
  dconf.settings."org/gnome/desktop/interface".show-battery-percentage = lib.mkDefault true;
}
