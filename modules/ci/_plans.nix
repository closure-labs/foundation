# Public check names are flake targets; Python consumes their generated projection.
{
  full.checks = ["home" "profile-command" "nixgl-wrapper" "desktop-icons" "profile-generation" "check-flake-file" "ci-graph"];
  automation.checks = ["profile-generation" "check-flake-file" "ci-graph"];
}
