# Public check names are flake targets; Python consumes their generated projection.
{
  full.checks = [
    "home"
    "password-managers"
    "profile-command"
    "nixgl-wrapper"
    "desktop-icons"
    "profile-generation"
    "check-flake-file"
    "ci-graph"
    "consumer-template"
  ];
  automation.checks = [
    "profile-generation"
    "check-flake-file"
    "ci-graph"
  ];
}
