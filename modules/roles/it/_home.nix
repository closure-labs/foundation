{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/it"; }) ];
  home.sessionVariables.FINITE_ROLE_IT = "1";
}
