# Driving Sprites remotely

The `sprite` CLI is the control plane for sprites you are not inside. It talks
to `https://api.sprites.dev` and nearly every command needs a target sprite.

If `/.sprite/api.sock` exists you are already inside a sprite; use `sprite-env`
instead — see the main skill and [environment-detection.md](environment-detection.md).

## Setup

```bash
# Install (macOS, Linux, Windows). Lands in ~/.local/bin.
curl -fsSL https://sprites.dev/install.sh | sh

# Interactive: browser flow against your Fly.io account
sprite org auth

# Non-interactive (CI): token format org-slug/org-id/token-id/token-value
sprite auth setup --token "$SPRITES_TOKEN"
```

Credentials live in `~/.sprites/sprites.json`, with the token in the system
keyring by default. `SPRITE_TOKEN` overrides everything and puts the CLI in a
stateless mode that writes no config — that is the right choice for CI.

`Error: no organizations configured` means authentication, not a bug. Stop and
tell the user to run `sprite org auth`; never paste a token into the shell on
their behalf or invent one.

## Choosing the target sprite

In precedence order:

1. `-s <name>` on the command.
2. A `.sprite` file in the working directory, written by `sprite use <name>`.
   It records `{"organization": ..., "sprite": ...}`. Add it to `.gitignore`.
3. Nothing — the command fails and asks for a name.

Add `-o <org>` when the account has more than one organization, or set
`SPRITE_ORG`. Get real names from `sprite list`; never guess one.

## Lifecycle

```bash
sprite list                       # names, state, URLs
sprite list --prefix dev          # filter
sprite create my-task             # create, then open a console
sprite create --skip-console my-task
sprite destroy -s my-task         # prompts; --force skips
```

Pick a short, task-scoped name. If a restricted token rejects the name and
demands a prefix, read the required prefix out of the error and retry once —
do not assume `mcp-` or any other fixed value.

`destroy` is irreversible and removes the filesystem, services, checkpoints,
and URL. Require explicit intent from the user. Never clean up sprites that
merely look stale.

## Running commands

```bash
sprite exec -s dev -- ls -la
sprite exec -s dev --dir /app -- npm test
sprite exec -s dev --env "NODE_ENV=test,CI=1" -- npm test
sprite console -s dev            # interactive shell
```

Everything after `--` is the command and its arguments. For shell syntax —
pipes, redirection, globs, heredocs — invoke the shell explicitly:

```bash
sprite exec -s dev -- bash -lc 'grep -c TODO src/*.ts | sort'
```

Useful flags: `--tty` for interactive programs, `--file <src:dest>` to upload a
file before running, `--no-port-forward` to stop the CLI forwarding ports the
command opens.

Each `exec` becomes a session. `sprite sessions list`, `sprite sessions attach
<id>`, and `sprite sessions kill <id>` manage them. Non-TTY sessions suspend on
detach and resume on reattach, so output is not lost.

Anything that must outlive the command — a server, a worker, a database — is a
service, not an exec. See [services.md](services.md).

## Files

```bash
sprite file push -s dev ./app.conf /etc/app.conf
sprite file pull -s dev /var/log/app.log ./logs/
sprite file edit -s dev /etc/app.conf
```

Prefer `git clone` inside the sprite over pushing a working tree. Never push
`.git/`, `node_modules/` and other dependency caches, `.env` files, key
material, or shell history. See
[files.md](files.md) for the full boundary list and for the
`fs` HTTP endpoints.

## Ports and URLs

```bash
sprite proxy -s dev 8080          # local 8080 -> sprite 8080
sprite proxy -s dev 3001:3000     # local 3001 -> sprite 3000
sprite url -s dev                 # URL and auth mode
```

`sprite proxy` is for reaching a sprite port privately from your machine. The
sprite's own `https://<sprite>-<org>.sprites.app/` URL is the public path, and
it routes to the service holding `--http-port`.

Newer CLI builds deprecate `sprite url` in favour of `sprite info` for reading
and `sprite config update --url-auth public|sprite` for changing the mode. Try
the documented form, and follow the deprecation notice if the binary prints
one.

## Raw API access

`sprite api` signs a request with your stored token, which beats hand-rolling
curl:

```bash
sprite api /v1/sprites
sprite api "/v1/sprites/dev/services"
```

For a direct HTTP client, see
[http-api.md](http-api.md): base URL
`https://api.sprites.dev`, header `Authorization: Bearer <org-token>`.

## Report back

State the sprite name, what ran, the exit status, the URL and its auth mode if
you exposed anything, and any checkpoint you created. A remote result the user
cannot locate afterwards is not a finished task.
