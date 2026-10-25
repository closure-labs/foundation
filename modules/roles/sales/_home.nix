{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/sales"; }) ];
  home.sessionVariables.FINITE_ROLE_SALES = "1";
}
