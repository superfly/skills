# HTTP API

For agents with an HTTP client but no CLI. Two surfaces: the local socket
inside a sprite, and the remote API at `api.sprites.dev`.

## Local socket (inside a sprite)

```bash
curl -s --unix-socket /.sprite/api.sock -H "Content-Type: application/json" \
  http://sprite/v1/services
```

No authentication — any process in the sprite may call it. The host in the URL
is ignored.

| Method + path | Purpose |
| --- | --- |
| `GET /info` | `{version, sprite_name, sprite_url, sprite_id, org}` |
| `GET /v1/services` | List services |
| `GET /v1/services/{name}` | One service |
| `PUT /v1/services/{name}` | Create or update; streams NDJSON |
| `DELETE /v1/services/{name}` | Delete |
| `POST /v1/services/{name}/start\|stop\|restart` | Streams NDJSON |
| `POST /v1/services/signal` | `{"name": ..., "signal": "TERM"}` |
| `POST /v1/checkpoint` | Create; body `{"comment": ...}`; streams NDJSON |
| `GET /v1/checkpoints` | List; `?history=<ver>` |
| `GET /v1/checkpoints/{id}` | One checkpoint |
| `DELETE /v1/checkpoints/{id}` | Delete |
| `POST /v1/checkpoints/{id}/restore` | `202 Accepted`, then the environment restarts |
| `GET /policy/network` | Read egress policy. **Read-only here by design** |
| `GET /v1/orgs` | Organizations reachable with injected tokens |
| `ANY /v1/orgs/{org}/...` | Authenticated proxy to the remote API |

There is no service-logs route on the socket. Read logs from
`/.sprite/logs/services/` instead.

## Remote API (outside a sprite)

Base URL `https://api.sprites.dev`, override with `SPRITE_URL` or
`SPRITES_API_URL`. Every request carries:

```
Authorization: Bearer <org-token>
```

The org token has the form `org-slug/org-id/token-id/token-value`. Mint one at
`sprites.dev/account`. Never log it, commit it, or echo it into output.

### Sprites

| Method + path | Purpose |
| --- | --- |
| `POST /v1/sprites` | Create. `{"name", "config": {ram_mb, cpus, region, storage_gb}, "environment": {}, "labels": []}` |
| `GET /v1/sprites` | List. Query `prefix`, `max_results`, `continuation_token` |
| `GET /v1/sprites/{name}` | One sprite |
| `PUT /v1/sprites/{name}` | Update `url_settings` (`auth`: `public`\|`sprite`, `private_access`: `admins`\|`org_users`) and `labels` |
| `DELETE /v1/sprites/{name}` | Destroy. Irreversible |

Everything below is scoped to one sprite and mirrors the socket routes with
`/v1/sprites/{name}` prepended.

### Exec

| Method + path | Purpose |
| --- | --- |
| `POST /v1/sprites/{name}/exec` | Run a command. Query `cmd` (repeatable: executable then each argument), `dir`, `path`, `env` (repeatable `K=V`), `stdin=true` with the body as stdin |
| `GET /v1/sprites/{name}/exec` | List active sessions |
| `POST /v1/sprites/{name}/exec/{session_id}/kill` | Query `signal` (default `SIGTERM`), `timeout` (default `10s`) |
| `WSS /v1/sprites/{name}/exec` | Interactive/TTY exec |

The HTTP exec response is a framed `application/octet-stream`: each chunk is
prefixed `0x01` for stdout or `0x02` for stderr, and the stream ends with
`0x03` followed by one exit-status byte. Decode the frames; do not treat the
body as plain text.

Pass the executable and each argument as separate `cmd` values. To use shell
syntax, make the shell the executable: `cmd=bash&cmd=-lc&cmd=<script>`.

### Services

| Method + path | Purpose |
| --- | --- |
| `GET .../services` | List |
| `GET .../services/{svc}` | One |
| `PUT .../services/{svc}` | Create or update. Body `{cmd, args[], env{}, dir, needs[], http_port}` |
| `DELETE .../services/{svc}` | Delete |
| `POST .../services/{svc}/start\|stop\|restart` | Query `duration` (default `5s`) or `timeout` (default `10s`) |
| `GET .../services/{svc}/logs` | Query `lines`, `duration` to follow |
| `POST .../services/signal` | `{"name", "signal"}` |

`cmd` is the executable only; arguments go in `args`.

### Checkpoints

| Method + path | Purpose |
| --- | --- |
| `POST .../checkpoint` | Create. `{"comment": ...}` |
| `GET .../checkpoints` | List; `?history=<ver>` |
| `GET .../checkpoints/{id}` | One, e.g. `v7` |
| `POST .../checkpoints/{id}/restore` | Restore. Destroys later state |

### Policy

| Method + path | Purpose |
| --- | --- |
| `GET .../policy/network` | Read rules |
| `POST .../policy/network` | **Replace** all rules |
| `GET\|POST\|DELETE .../policy/privileges` | Capabilities and devices |
| `GET\|POST\|DELETE .../policy/resources` | Memory limits |

### Filesystem

| Method + path | Purpose |
| --- | --- |
| `GET .../fs/read` | Query `path`, `workingDir`. Returns raw bytes |
| `PUT .../fs/write` | Query `path`, `workingDir`, `mode`, `mkdirParents` (default true), `asRoot`. Body is raw bytes |
| `GET .../fs/list` | Directory entries |
| `DELETE .../fs/delete` | Query `path`, `workingDir`, `recursive`, `asRoot` |
| `POST .../fs/rename\|copy\|chmod\|chown` | JSON bodies with `source`/`dest` or `path` |
| `WSS .../fs/watch` | Subscribe to change events |

### Other

| Method + path | Purpose |
| --- | --- |
| `WSS .../proxy` | TCP tunnel. First message `{"host", "port"}`, then raw bytes |
| `WSS .../ports/watch` | Port open/close events |
| `GET /v1/gateway/list` | Third-party API connections (call from inside the sprite) |

## Streaming responses

Create, start, stop, restart, checkpoint, and restore stream newline-delimited
JSON: `{"type": "info"|"stdout"|"stderr"|"error"|"complete", "data"|"error",
"time"}`. Service log events use `{"type": "stdout"|"stderr"|"exit"|"started"|
"stopping"|"stopped", "data"|"exit_code", "timestamp"}` with a Unix-millisecond
timestamp.

Read to the terminating event before declaring success. A `200` on the request
says the operation started, not that it worked.

## Notes

- There is no published OpenAPI document. Treat the CLI and the SDKs (Go,
  JavaScript, Python, Elixir) as the authoritative wire format.
- `sprite api <path> -- [curl options]` signs a request with the stored token
  and is easier than assembling headers yourself.
- The sprite's own URL, `https://<sprite-name>-<org>.sprites.app/`, is a
  separate surface from the API. With `auth: sprite` it needs an org bearer
  token; with `auth: public` it needs nothing.
