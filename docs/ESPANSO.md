# Personal Espanso files

Enable the Support role or `support-tools` capability, then keep personal matches in your own repository. The host must provide the keyboard access Espanso needs; Foundation does not grant it.

## 1. Pin a snapshot

Fetch the repository as your desktop user to discover its commit and content hash:

```sh
nix eval --impure --json --expr 'builtins.fetchTree {
  type = "git";
  url = "ssh://git@example.com/your/espanso-config.git";
  ref = "main";
}'
```

Replace the example URL before running it. Private sources use your SSH credentials.

## 2. Declare the files

Add this to `~/.config/home-manager/modules/local.nix`, replacing the URL, commit and hash with real values:

```nix
{ ... }: let
  matches = builtins.fetchTree {
    type = "git";
    url = "ssh://git@example.com/your/espanso-config.git";
    ref = "main";
    rev = "FULL_COMMIT_HASH";
    narHash = "NAR_HASH";
  };
in {
  xdg.configFile."espanso/match/packages/personal.yml".source =
    "${matches.outPath}/personal.yml";
}
```

Declare other files individually under `espanso/config/`, `espanso/match/` or `espanso/scripts/`. Avoid defining the same target in two modules. Existing unmanaged files may need to be moved aside before Home Manager can manage them.

## 3. Build and apply

Follow [Build, then activate](ACTIVATION.md#build-then-activate) to apply the updated personal source.

Commit the pins in your personal configuration. To update matches, commit and push their source, discover the new hashes, update the pins, then build and apply again. Editing a working checkout alone does not change the active snapshot.

Fetched files enter the Nix store, so keep credentials outside matchfiles. See [Configuration](CONFIGURATION.md) for other personal settings.
