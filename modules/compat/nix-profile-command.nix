# Remove when the pinned Home Manager resolves:
# https://github.com/nix-community/home-manager/issues/9598
{lib, ...}: let
  modernize = script:
    if lib.hasInfix "run $oldNix profile install $1" script
    then
      ''
        foundationNixProfileCommand=install
        if nix profile add --help >/dev/null 2>&1; then
          foundationNixProfileCommand=add
        fi
      ''
      + lib.replaceStrings
      ["run $oldNix profile install $1" ''INSTALL_CMD="nix profile install"'']
      [''run "$oldNix" profile "$foundationNixProfileCommand" "$1"'' ''INSTALL_CMD="nix profile $foundationNixProfileCommand"'']
      script
      + ''
        unset foundationNixProfileCommand
      ''
    else script;
in {
  # Transform only this DAG entry after merging; retain the upstream installer,
  # custom activation hooks, ordering, and legacy nix-env profile support.
  options.home.activation = lib.mkOption {
    apply = lib.mapAttrs (name: entry:
      if name == "installPackages"
      then entry // {data = modernize entry.data;}
      else entry);
  };
}
