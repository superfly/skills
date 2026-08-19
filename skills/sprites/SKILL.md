---
name: sprites
description: Use this skill for Sprites — isolated, persistent cloud Linux environments from Fly.io with their own filesystem, URL, services, checkpoints, and network policy. Trigger it to create, list, inspect, or destroy sprites, to run builds/tests/agents in a remote sandbox, to expose a preview URL, to snapshot and roll back state, or whenever the user names Sprites, sprite-env, or sprites.dev. It works both from inside a sprite and from a machine outside one.
license: MIT
metadata:
  author: Fly.io
  version: "1.0.0"
  homepage: https://sprites.dev
---

# Sprites

A sprite is a persistent, hardware-isolated Linux environment. It keeps its
filesystem between sessions, gets a public hostname, runs services that survive
disconnects, and can be snapshotted and restored in seconds.

**Before anything else, work out where you are running.** Every command in this
skill family has two forms, and picking the wrong one wastes a turn.

## Step 1: detect the context

```bash
test -S /.sprite/api.sock && echo inside || echo outside
```

| Result | Meaning | Control plane to use |
| --- | --- | --- |
| `inside` | The agent is running *in* the sprite | `sprite-env` CLI at `/.sprite/bin/sprite-env` |
| `outside` | The agent is on a laptop, CI runner, or another host | `sprite` CLI, the Sprites MCP server, or the REST API |

Cache the answer for the session; it cannot change mid-session.

The two control planes are not interchangeable:

- `sprite-env` talks to the local API socket. It always acts on **this** sprite
  and takes no sprite name. It cannot see or touch other sprites.
- `sprite` talks to `https://api.sprites.dev` over the network. Nearly every
  command needs a target sprite (`-s <name>`), and it can create and destroy
  sprites.

Do not call `sprite-env` from outside a sprite, and do not use the remote MCP
tools or `sprite -s <self>` from inside a sprite to manage the sprite you are
already in. See [environment detection](references/environment-detection.md)
for the fallbacks when neither binary is installed.

## Step 2: pick the smallest operation

| Goal | Inside a sprite | Outside a sprite |
| --- | --- | --- |
| Identify the environment | `sprite-env info` | `sprite list`, `sprite url -s <name>` |
| Run a command | Run it directly in the shell | `sprite exec -s <name> -- <cmd>` |
| Keep a process alive | `sprite-env services create ...` | `sprite exec -s <name> -- sprite-env services create ...` |
| Snapshot state | `sprite-env checkpoints create` | `sprite checkpoint create -s <name>` |
| Move files in or out | Ordinary file tools, or `git clone` | `sprite file push` / `sprite file pull` |
| Reach an external API | The gateway at `api.sprites.dev` | Run the gateway call inside the sprite |
| Create or delete an environment | Not possible | `sprite create` / `sprite destroy` |

Detailed procedures live in the companion skills: `sprites-remote`,
`sprites-services`, `sprites-checkpoints`, `sprites-network-policy`, and
`sprites-api-gateway`.

## Golden path

1. Detect inside or outside. Choose the control plane once.
2. Identify the exact sprite by name. From outside, get it from `sprite list` or
   from `.sprite/config` (`sprite use`); never guess a name.
3. Inspect before you mutate. Read service state, logs, or checkpoint lists
   first.
4. Checkpoint valuable state before risky work. Checkpoints take seconds.
5. Do the work: `exec` for bounded commands, a service for anything that must
   outlive the call.
6. Verify with real output — exit status, service state, logs, an HTTP probe.
7. Report the sprite name, the URL and its auth mode, and any checkpoint IDs.

## Safety rules

- A sprite URL may be public. Never serve environment variables, tokens, key
  files, unfiltered logs, or admin endpoints from a sprite service.
- `checkpoint restore` rewinds the filesystem and discards later changes.
  Explain that and get approval before running it.
- `destroy` is irreversible and takes the services, checkpoints, and URL with
  it. Require explicit intent.
- Network policy updates **replace** the whole rule set. Read the current
  policy, merge, then write.

Full detail in [safety](references/safety.md).

## References

- [environment-detection.md](references/environment-detection.md) — deciding
  inside vs outside, installing either CLI, and auth setup.
- [cli.md](references/cli.md) — the full `sprite-env` and `sprite` command
  surface.
- [http-api.md](references/http-api.md) — REST endpoints behind both CLIs, for
  agents with only an HTTP client.
- [files.md](references/files.md) — moving code and data in and out.
- [safety.md](references/safety.md) — confirmation rules and exposure limits.
