{
  inputs.foundation.url = "github:closure-labs/foundation/main";
  outputs = inputs: let
    profile = builtins.fromJSON (builtins.readFile ./profile.json);
  in {
    homeConfigurations.${profile.identity.username} = inputs.foundation.lib.mkHomeConfiguration {
      inherit profile;
      modules = [./customize.nix ./modules/local.nix];
      extraInputs = builtins.removeAttrs inputs ["self" "foundation"];
    };
  };
}
