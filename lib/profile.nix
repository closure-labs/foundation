{
  pkgs,
  source,
}:
pkgs.writeShellApplication {
  name = "finite-home-profile";
  runtimeInputs = with pkgs; [python3 nix yq-go];
  text = ''
    exec python3 ${source}/scripts/home.py profile "$@"
  '';
}
