{ lib, foundationComposition, ... }: {
  home.sessionVariables = lib.genAttrs
    (map (role: "FINITE_ROLE_${lib.toUpper role}") foundationComposition.profile.roles) (_: "1");
}
