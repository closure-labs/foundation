{ lib, pkgs, ... }: let
  camera = import ./_package.nix { inherit pkgs; };
in {
  # Runtime hardware checks must not make pure home evaluation host-dependent.
  # Never restart WirePlumber during activation: this can interrupt a live call.
  home.activation.foundationIpu7 = lib.hm.dag.entryAfter ["writeBoundary"] ''
    if ! run ${camera}/bin/foundation-camera --repair; then
      echo "Foundation: IPU7 camera needs attention; run foundation home camera." >&2
    fi
  '';
}
