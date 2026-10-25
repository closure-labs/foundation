{ pkgs, ... }: let espanso = pkgs.espanso-wayland; in {
  systemd.user.services.espanso = {
    Unit = {
      Description = "Espanso text expander";
      After = ["graphical-session.target"];
      PartOf = ["graphical-session.target"];
    };
    Service = {
      ExecStart = "${espanso}/bin/espanso launcher";
      Restart = "on-failure";
      RestartSec = 3;
    };
    Install.WantedBy = ["graphical-session.target"];
  };
}
