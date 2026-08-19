---
name: sprites-services
description: Use this skill to run long-lived processes in a Sprite — web servers, APIs, workers, databases, queues, agents — and to expose one of them on the sprite's public URL. Trigger it for "start the dev server", "keep this running", "give me a preview URL", restarting or stopping a service, or reading service logs. Services survive disconnects and reboots; a plain background command does not.
license: MIT
metadata:
  author: Fly.io
  version: "1.0.0"
---

# Sprites services

A service is a supervised process. The sprite restarts it after a reboot, keeps
it alive when your session ends, and routes HTTP to it. Anything that must
outlive the command that started it belongs here.

**Never start a long-running process with `&`, `nohup`, `screen`, or `tmux` in
a sprite.** There is no systemd. The service manager is the supervisor, and a
detached process is invisible to it, dies on reboot, and cannot receive proxied
HTTP.

## Command form

Inside a sprite, `sprite-env` is the tool. From outside, run the same command
through `sprite exec`, or use the equivalent MCP tool if your client has the
Sprites MCP server connected.

| Action | Inside | Outside |
| --- | --- | --- |
| List | `sprite-env services list` | `sprite exec -s <n> -- sprite-env services list` |
| Inspect one | `sprite-env services get <svc>` | `sprite exec -s <n> -- sprite-env services get <svc>` |
| Create | `sprite-env services create <svc> ...` | same, via `sprite exec` |
| Start / stop | `sprite-env services start\|stop <svc>` | same, via `sprite exec` |
| Restart | `sprite-env services restart <svc>` | same, via `sprite exec` |
| Signal | `sprite-env services signal <svc> HUP` | same, via `sprite exec` |
| Delete | `sprite-env services delete <svc>` | same, via `sprite exec` |

## Creating a service

```bash
sprite-env services create web --cmd /usr/bin/node --args server.js --http-port 3000
```

Options for `create`:

| Flag | Meaning |
| --- | --- |
| `--cmd <path>` | The executable **only**. Required. |
| `--args <a,b,c>` | Comma-separated arguments. |
| `--env <K=v,K2=v2>` | Comma-separated environment variables. |
| `--dir <path>` | Working directory. |
| `--needs <svc1,svc2>` | Services that must start first. |
| `--http-port <port>` | Receive proxied HTTP on this port. One service only. |
| `--duration <time>` | How long to stream logs after creation (default `5s`). |
| `--no-stream` | Do not stream logs after creation. |

The single most common mistake is packing arguments into `--cmd`:

```bash
# WRONG — the whole string is treated as one executable path
sprite-env services create web --cmd "python3 -m http.server 8080"

# RIGHT
sprite-env services create web --cmd python3 --args "-m,http.server,8080" --http-port 8080
```

Use `sprite-env services restart <svc>` to restart. Do not run `stop` then
`start` as two commands; the restart subcommand exists and is atomic.

## HTTP exposure

- The proxy routes the sprite's URL to port `8080` by default, or to the port of
  the service that declares `--http-port`.
- **Only one service** may hold an HTTP port at a time.
- A service with an HTTP port auto-starts when a request arrives, so an idle
  sprite still answers its URL.
- Get the URL with `sprite-env info` (inside) or `sprite url -s <name>`
  (outside).

Default to `--http-port 8080` unless the user asks for another port.

### The URL may be public

Two auth modes exist: `sprite` (organization members only, the default) and
`public` (open to the internet). Change it with
`sprite url update --auth public` — and confirm with the user first, because it
publishes everything the service serves.

Whatever the mode, never let a sprite service expose environment dumps,
credentials, key files, arbitrary file browsing, unfiltered logs, or debug and
admin endpoints.

## Workflow

1. `services list` before adding anything; the service may already exist.
2. Pick a stable role name: `web`, `api`, `worker`, `db`, `preview`.
3. `create` with an explicit `--cmd`, `--args`, and `--http-port` where needed.
4. Read the streamed logs from that start. Do not predict success — report what
   the logs actually said.
5. Verify with `services get <svc>` and an HTTP probe of the URL when it serves
   HTTP.
6. Report the service name, state, port, URL, and auth mode.

When a start fails, read the logs before editing the definition. Delete and
recreate only when the command, args, or port must change; use `restart` for a
code change.

## Cleanup

Stop or delete only the services in scope for the current task. Leaving an idle
service is fine — the sprite pauses when idle and the service restarts on the
next request.
