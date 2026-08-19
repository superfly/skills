# CLI reference

Two binaries, two scopes. `sprite-env` acts on the sprite it runs in.
`sprite` acts on a named remote sprite.

## `sprite-env` — inside a sprite

Located at `/.sprite/bin/sprite-env`.

```
sprite-env info                 # name, id, org, URL, version (JSON)
sprite-env version              # environment version
sprite-env curl <path>          # raw request to the local API socket
sprite-env services <sub>
sprite-env checkpoints <sub>
```

### Services

| Command | Notes |
| --- | --- |
| `services list` | All services with state |
| `services get <name>` | One service |
| `services create <name> [opts]` | See flags below |
| `services delete <name>` | Removes the definition |
| `services start\|stop <name>` | `stop` sends TERM |
| `services restart <name>` | Use this, not stop+start |
| `services signal <name> <SIG>` | e.g. `TERM`, `HUP`, `KILL` |

`create` flags: `--cmd <executable>` (required, binary only), `--args
"a,b,c"`, `--env "K=v,K2=v2"`, `--dir <path>`, `--needs "svc1,svc2"`,
`--http-port <port>` (one service at a time), `--duration <time>` (log stream
length, default `5s`), `--no-stream`.

### Checkpoints

| Command | Notes |
| --- | --- |
| `checkpoints list [--history <ver>]` | IDs are `v0`, `v1`, … |
| `checkpoints get <id>` | Details for one |
| `checkpoints create [--comment <msg>]` | Always pass a comment |
| `checkpoints restore <id>` | Async; restarts the environment |

## `sprite` — outside a sprite

Global flags on nearly every command: `-o, --org <name>`, `-s, --sprite
<name>`, `-h, --help`.

### Authentication

| Command | Notes |
| --- | --- |
| `sprite org auth [--org <name>]` | Browser flow via Fly.io |
| `sprite org list` | Configured orgs and tokens |
| `sprite org logout [--force]` | Remove tokens |
| `sprite org keyring disable\|enable` | Keyring vs file storage |
| `sprite auth setup --token <t>` | Non-interactive; `org-slug/org-id/token-id/token-value` |
| `sprite logout` | Remove all Sprites configuration |

### Lifecycle

| Command | Notes |
| --- | --- |
| `sprite create [name]` | `--skip-console`, `--label <l>` (repeatable) |
| `sprite list` | `--prefix <p>`, `-w/--watch` |
| `sprite use [name]` | Writes `.sprite` in the directory; `--unset` removes it |
| `sprite destroy [name]` | `--force` skips the prompt. Irreversible |
| `sprite upgrade` | `--check`, `--force`, `--version`, `--channel` |

### Commands and sessions

| Command | Notes |
| --- | --- |
| `sprite exec [flags] -- <cmd> [args]` | `--dir`, `--env "K=v,K2=v2"`, `--tty`, `--file <src:dest>`, `--no-port-forward`, `--http-post` |
| `sprite console` | Interactive shell |
| `sprite sessions list\|attach <id>\|kill <id>` | Non-TTY sessions suspend on detach and resume on attach |

### Checkpoints

| Command | Notes |
| --- | --- |
| `sprite checkpoint create [--comment <t>]` | |
| `sprite checkpoint list` | `--history <ver>`, `--include-auto` |
| `sprite checkpoint info <id>` | |
| `sprite checkpoint delete <id>` | Not available through MCP |
| `sprite restore <id>` | Alias of `checkpoint restore` |

### Files, ports, URL

| Command | Notes |
| --- | --- |
| `sprite file push <local> <remote>` | |
| `sprite file pull <remote> <local>` | |
| `sprite file edit <remote>` | |
| `sprite proxy <port>` or `<local:remote>` | Multiple ports allowed; `-W/--stdio <[host]:port>` |
| `sprite url` | URL and auth mode |
| `sprite url update --auth public\|sprite` | Changes who can reach the URL |
| `sprite api <path> -- [curl options]` | Authenticated raw API call |

Newer builds deprecate `sprite url` in favour of `sprite info` for reading and
`sprite config update --url-auth public|sprite [--private-access
admins|org_users]` for changing it. Follow the deprecation notice the binary
prints.

### Exit codes

`0` success, `1` general error, `2` command not found, `126` cannot execute,
`127` not found inside the sprite, `128+n` terminated by signal `n`.
