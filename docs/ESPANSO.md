## Manage Git-backed Espanso files without custom flake inputs

Keep Espanso files in a separate Git repository and declare their pinned snapshot
in `~/.config/home-manager/modules/local.nix`. Finite preserves that module during
scaffold upgrades. This keeps personal sources independent of the template's
`flake.nix` and `flake.lock`:

```nix
{...}: let
  matches = builtins.fetchTree {
    type = "git";
    url = "ssh://git@example.com/your/espanso-config.git";
    ref = "main";
    rev = "REPLACE_WITH_FULL_COMMIT_HASH";
    narHash = "REPLACE_WITH_NAR_HASH";
  };
in {
  xdg.configFile."espanso/match/packages/personal.yml".source =
    "${matches.outPath}/personal.yml";
}
```

Use real commit and content hashes before building. To inspect a new snapshot,
fetch it explicitly as your desktop user:

```bash
nix eval --impure --json --expr 'builtins.fetchTree {
  type = "git";
  url = "ssh://git@example.com/your/espanso-config.git";
  ref = "main";
}'
```

Copy the returned `rev` and `narHash` into `modules/local.nix`, review the change,
then build and apply Home Manager. Only the discovery command uses `--impure`;
the pinned module works with normal pure flake evaluation. Keep the module in
your personal configuration Git repository as well, so reverting its pins restores
the previous snapshot. Home Manager links the snapshot into Espanso's normal
configuration directory; edits in a working checkout do not affect the running
configuration until you commit, update the pins, and activate it.

Declare additional files under `espanso/config/`, `espanso/match/`, or
`espanso/scripts/` individually. Manage only the files you intend to own; existing
unmanaged files need to be moved aside before their first Home Manager activation.
If `customize.nix` already declares a target, move that declaration into the local
module rather than defining it twice. Once migrated, remove its former custom
flake input and run `nix flake lock ~/.config/home-manager` to prune unused entries
without requesting dependency updates.

Private repositories use your SSH credentials during source fetching. A
`file:///absolute/path/to/checkout` URL also works with explicit pins, but restoring
on another machine requires that checkout and commit. Push local-only commits
before switching to an SSH remote. As with flake inputs, fetched files enter the
Nix store; keep credentials outside matchfiles.

