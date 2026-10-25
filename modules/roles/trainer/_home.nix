{ ... }: {
  imports = [ (import ../../profiles/composition/_legacy-applications.nix { id = "roles/trainer"; }) ];
  home.sessionVariables.FINITE_ROLE_TRAINER = "1";
}
