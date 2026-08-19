---
name: sprites-api-gateway
description: Use this skill when work inside a Sprite needs an external API — GitHub, Slack, Linear, Discourse, S3-compatible storage, or any token-authenticated service. The Sprites API gateway at api.sprites.dev injects credentials for you, so a sprite never holds raw API keys. Trigger it for third-party integrations, authenticated API calls from a sprite, or "how do I give this sprite access to X".
license: MIT
metadata:
  author: Fly.io
  version: "1.0.0"
---

# Sprites API gateway

The gateway proxies outbound API calls and adds the credentials on the way
through. It is the supported way for a sprite to reach a third-party API.

Requests are authenticated by the sprite's own identity, so **the call must
originate inside the sprite**. From outside, run it through the sprite:

```bash
sprite exec -s <sprite> -- curl -s https://api.sprites.dev/v1/gateway/list
```

Never ask the user for an API key, and never write one into the sprite's
filesystem, when a gateway connection can do the job.

## Step 1: discover the connections

```bash
curl -s https://api.sprites.dev/v1/gateway/list
```

The response has two arrays:

- `connections` — live, authenticated integrations, ready to call.
- `available` — providers the user can connect but has not connected yet.

Always list first. Do not guess a gateway URL.

## Step 2: match the request to a connection

Each entry in `connections` carries:

| Field | Use |
| --- | --- |
| `provider` | Match on this first (`github`, `slack`, `linear`, …) |
| `display_name`, `description` | Match when the provider name is ambiguous |
| `gateway_base_url` | The base URL for every request to that provider |
| `scopes` | Permissions already granted |
| `usage_snippet` | A working example to adapt |
| `request_scopes_url` | Where the user grants more scopes |

## Step 3: call the API

Append the provider's API path to `gateway_base_url`:

```bash
curl -s https://api.sprites.dev/v1/gateway/github/user/repos
```

Send **no** `Authorization` header, API key, or token. The gateway adds them.
Adding your own credential is the most common failure here, and it usually
produces a confusing 401 rather than an obvious error.

## Step 4: handle the two failure modes

**Missing scope.** Compare the operation against the connection's `scopes`.
Name the specific scopes needed and why, then send the user to
`request_scopes_url`. Do not retry the call in a loop.

**No connection.** Look for the provider in `available`, share its `setup_url`,
and say what the connection will enable. After the user finishes setup, re-run
the list command — the new connection appears in `connections` with its own
base URL.

If the provider is in neither array, the gateway does not support it. Offer
`custom_api`, which connects any token-authenticated HTTP API, rather than
falling back to a raw key inside the sprite.

## Rules

- Discover before calling. The base URL varies per connection.
- Never add authentication headers of your own.
- Never ask for, log, echo, or store raw credentials.
- Keep gateway responses out of any HTTP surface the sprite serves; they can
  contain private repository, message, or account data.
