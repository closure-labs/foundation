{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/executive"; }) ];
  home.sessionVariables.FINITE_ROLE_EXECUTIVE = "1";
}
