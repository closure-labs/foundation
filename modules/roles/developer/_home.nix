{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/developer"; }) ];
  home.sessionVariables.FINITE_ROLE_DEVELOPER = "1";
}
