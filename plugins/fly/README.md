![Fly.io](assets/logo.svg)

# Fly

Launch, deploy, configure, scale and troubleshoot apps on [Fly.io](https://fly.io)
from your coding agent. One skill covers flyctl, the hosted
[Fly MCP](https://mcp.fly.io) server and Sprites, Fly's persistent remote Linux
environments.

## What it does

- **Launch and deploy**: `fly launch`, `fly deploy`, strategies, release
  commands, rollbacks, and how to verify a deploy actually worked.
- **Configure**: the full `fly.toml` reference, services, health checks,
  processes, autostop and autostart.
- **Scale**: Machine counts per region and process group, VM sizes, memory.
- **Operate**: status, logs, SSH, console, and troubleshooting playbooks for
  502s, crash loops, OOM kills, port binding and failing certificates.
- **Resources**: Machines, volumes and snapshots, secrets, IPs, certificates
  and custom domains, private networking, Managed Postgres, Tigris object
  storage, Upstash Redis.
- **Sprites**: create and drive remote environments from inside or outside,
  services and preview URLs, checkpoints, network policy, the API gateway.
- **Safety**: read before write, confirm before destroy, verify after every
  change, never echo a secret.

## Install

Claude Code, from this repository's marketplace:

```text
/plugin marketplace add superfly/skills
/plugin install fly@fly-skills
```

Any agent that supports the Agent Skills format:

```bash
npx skills add superfly/skills
```

Codex, Cursor, Grok Build and Antigravity install through their marketplaces;
see the [repository README](../../README.md).

## First use

Ask for something concrete: "deploy this app to Fly", "why is my Fly app
returning 502", "add a Postgres database", "run the test suite in a sprite".
The skill checks for `fly`, signs you in through the browser if needed, and
routes to the right reference.

With the plugin installed, the hosted MCP server is connected as `fly`. The
first call opens browser consent, where you choose the organizations, apps,
Managed Postgres and Sprites permissions to grant. The grant is per resource
and never widens on its own; `get_fly_context` reports it. Nothing is created,
stopped or deleted just to prove the connection works.

## Runtime and data handling

- flyctl commands run locally with your own `fly auth login` session or
  `FLY_API_TOKEN`.
- The remote MCP server is `https://mcp.fly.io`. Calls send the arguments the
  requested operation needs to Fly.io and its product backends; those can
  include commands, file contents and secret values when you ask for those
  operations. The plugin adds no telemetry service or credential store.
- The `PreToolUse` hook (`scripts/fly_guard.py`) reads the proposed tool call
  from stdin and asks for confirmation before destructive, disruptive or
  billable operations, both MCP tools and `fly`/`sprite` shell commands. It
  runs no commands, reads no workspace files, makes no network requests and
  never repeats command arguments. If `python3` is missing from `PATH`, the
  hook skips inspection and emits a warning; normal client permissions still
  apply. A missing guard script or an unexpected guard error still blocks the
  call. It is a reminder, not a sandbox; server-side authorization and the MCP
  grant are the boundary.

See [safety](skills/fly/references/safety.md), the
[Fly MCP guide](https://mcp.fly.io/guide.md), the
[Fly.io privacy policy](https://fly.io/legal/privacy-policy/) and
[support](https://fly.io/support/).

## Validation

From the repository root:

```sh
python3 scripts/validate_skills.py
claude plugin validate ./plugins/fly --strict
```
