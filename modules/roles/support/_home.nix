{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/support"; }) ];
  home.sessionVariables.FINITE_ROLE_SUPPORT = "1";
}
