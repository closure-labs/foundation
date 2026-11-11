# Configuration

Your personal flake lives at `~/.config/home-manager`. Foundation provides shared defaults; you own the files that select and customize them.

| File | What to change |
| --- | --- |
| `profile.json` | Account identity, foundation, roles, capabilities, optional packages and host declarations |
| `customize.nix` | Personal packages and Home Manager settings |
| `modules/local.nix` | Additional local settings or pinned personal sources |
| `flake.nix` | Foundation source and any additional inputs |
| `flake.lock` | Exact source revisions; update through the chosen update workflow |

Keep account identity consistent with your login and leave `home.stateVersion` unchanged during routine updates.

## Change roles and applications

Open the selector:

```sh
foundation home configure
```

Review the choices and preview, then choose **Build and apply**. Cancelling leaves the configuration unchanged. Schema 3 supports both Professional and Personal roles, plus additional capabilities.

For the command line:

```sh
foundation home apply --roles developer,creative --packages jj --capabilities recording --preview
foundation home check --roles developer,creative --packages jj --capabilities recording
foundation home apply --roles developer,creative --packages jj --capabilities recording
```

`--preview` shows the proposed change. `--check` builds without activation. The final command applies the selections. Supplied lists replace those selections; omitted options preserve them. `--capabilities ''` clears explicit capabilities, but applications supplied by a role remain enabled.

See [Profiles and hardware](PROFILES.md) for the available choices and [Migration](MIGRATION.md) for older profiles.

## Add personal Nix settings

Add settings to an existing module, or replace the empty `modules/local.nix` with:

```nix
{ pkgs, ... }: {
  home.packages = [ pkgs.ripgrep ];
  programs.zsh.shellAliases.ll = "ls -lah";
}
```

Then [build and activate](ACTIVATION.md#build-then-activate) the updated configuration.

Home Manager merges these modules with Foundation's defaults. Review settings that override package providers or desktop launchers. Keep credentials outside Nix source files: fetched sources and generated configuration can enter the Nix store.

For pinned personal text-expansion files, see [Espanso](ESPANSO.md).

## Edit hardware

Edit the `host` object in `profile.json`, then run the build/apply commands above. The role selector preserves hardware declarations; it does not provide a hardware dialog. [Profiles and hardware](PROFILES.md#host-settings) lists supported fields and model constraints.

## Pin a source checkout

A personal flake can import an immutable local Git commit:

```nix
inputs.foundation.url = "git+file:///absolute/path/to/foundation?rev=FULL_COMMIT";
```

Replace the path and commit with real values, then update the lock from your personal configuration:

```sh
cd ~/.config/home-manager
nix flake update foundation
```

Then [build and activate](ACTIVATION.md#build-then-activate). The URL and lock must select the same immutable commit. Local Git sources use manual pin maintenance; the staged updater does not replace them with a remote commit. The checkout and commit must be available when rebuilding elsewhere.
