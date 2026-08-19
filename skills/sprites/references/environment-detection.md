# Inside or outside a sprite

Every Sprites operation has two forms. Decide which one applies before running
anything.

## The test

```bash
test -S /.sprite/api.sock && echo inside || echo outside
```

The socket at `/.sprite/api.sock` exists only in a sprite. It is a more
reliable signal than the presence of a binary, a hostname, or an environment
variable.

Secondary signals, useful for confirming:

| Signal | Inside a sprite |
| --- | --- |
| `/.sprite/` directory with `bin/`, `docs/`, `checkpoints/`, `policy/` | present |
| `/.sprite/bin/sprite-env` | present, and `sprite-env info` returns JSON |
| `/.sprite/llm.txt`, `/.sprite/docs/agent-context.md` | present |
| `~/.sprites/sprites.json` | usually absent |

## Inside: the local socket

`sprite-env` is a thin wrapper over the socket. Every call is the equivalent of:

```bash
curl -s --unix-socket /.sprite/api.sock -H "Content-Type: application/json" \
  http://sprite/v1/services
```

The host part of the URL is ignored. `sprite-env curl <path>` is a raw
pass-through, which is the escape hatch when a subcommand does not exist:

```bash
sprite-env curl /v1/checkpoints
sprite-env curl /policy/network
```

The socket is unauthenticated and world-accessible inside the sprite — any
process in the environment can drive it. That is why it exposes network policy
read-only.

`sprite-env` always means *this* sprite. It cannot list, create, or reach other
sprites.

## Outside: the `sprite` CLI

```bash
curl -fsSL https://sprites.dev/install.sh | sh    # installs to ~/.local/bin
sprite org auth                                    # browser flow via Fly.io
```

For CI, mint a token at `sprites.dev/account` and use one of:

```bash
sprite auth setup --token "org-slug/org-id/token-id/token-value"
export SPRITE_TOKEN="org-slug/org-id/token-id/token-value"   # stateless, no config written
```

Environment variables the CLI reads:

| Variable | Effect |
| --- | --- |
| `SPRITE_TOKEN` | Org API token. Highest priority; switches the CLI to stateless mode. |
| `SPRITE_ORG` | Organization when `-o` is not given. |
| `SPRITE_URL` | API base URL override, checked first. |
| `SPRITES_API_URL` | API base URL override, fallback. Default `https://api.sprites.dev`. |

Configuration on disk:

| Path | Contents |
| --- | --- |
| `~/.sprites/sprites.json` | Current org/API selection and org list. Token in the keyring by default. |
| `~/.sprites/config.json` | Legacy, migrated into `sprites.json`. |
| `.sprite` (per directory) | `{"organization": ..., "sprite": ...}`, written by `sprite use`. Git-ignore it. |

## Neither CLI is installed

Fall back in this order:

1. **Outside, no `sprite` binary** — install it with the script above, or call
   the REST API directly with an `Authorization: Bearer <org-token>` header.
   See [http-api.md](http-api.md).
2. **An MCP client with the Sprites server connected** — use the MCP tools
   (`list_sprites`, `exec`, `service_create`, `checkpoint_create`, …). They
   cover the same control plane and handle OAuth for you.
3. **Inside, no `sprite-env`** — talk to `/.sprite/api.sock` with curl.

Do not install the remote CLI inside a sprite to manage the sprite you are
already in, and do not register a second MCP server to work around a missing
binary.

## Nested case: outside-tooling inside a sprite

A sprite can hold credentials for an organization and manage *other* sprites.
In that case both tools are legitimately present: `sprite-env` for the local
environment and `sprite -s <other>` for the remote ones. Keep the distinction
explicit in what you report, or the user cannot tell which environment changed.
