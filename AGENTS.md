# Fly.io Agent Plugins

Agent plugins for [Fly.io](https://fly.io). Interact with Fly through one
orchestration skill, `fly`, and the hosted Fly MCP server.

## Plugin model

The shared plugin payload lives in `plugins/fly`.

- Claude Code: `plugins/fly/.claude-plugin/plugin.json`, `plugins/fly/.mcp.json`, and the repo marketplace at `.claude-plugin/marketplace.json`.
- OpenAI Codex: `plugins/fly/.codex-plugin/plugin.json`, `plugins/fly/.mcp.json`, and the repo marketplace at `.agents/plugins/marketplace.json`.
- Grok Build / xAI marketplace: resolves `plugins/fly` as the plugin via a remote source subpath, so the payload exposes `plugins/fly/.grok-plugin/plugin.json`, `plugins/fly/.grok-plugin/mcp.json`, `plugins/fly/skills` and `plugins/fly/hooks` directly.
- Cursor: `plugins/fly/.cursor-plugin/plugin.json`, `plugins/fly/.cursor-plugin/mcp.json`, and the repo marketplace at `.cursor-plugin/marketplace.json`.
- Google Antigravity: `plugins/fly/.antigravity-plugin/plugin.json` and `plugins/fly/mcp_config.json`, with `plugins/fly/README.md` as the pre-install page and `plugins/fly/assets/logo.svg` as the logo. Antigravity resolves every component path from `plugins/fly`, so only `plugin.json` lives in `.antigravity-plugin/`; its MCP config uses `serverUrl` and namespaces the server key as `fly-mcp`.
- skills.sh (`npx skills add superfly/skills`): discovers the skills through `.claude-plugin/marketplace.json` and `skills.sh.json`, since `plugins/*/skills/` is not one of its default scan paths.

Claude Code and Grok Build load `plugins/fly/hooks/hooks.json`, a `PreToolUse` hook that runs `scripts/fly_guard.py` for the plugin's MCP tools and for `Bash` calls. It returns an `ask` decision before destructive, disruptive or billable `fly`/`sprite` commands and MCP operations, and before Sprite exec commands that warrant a checkpoint. It never echoes command arguments (they can carry secret values). Antigravity does not load this hook.

## Skill model

The plugin ships two skills:

- `plugins/fly/skills/fly/SKILL.md`: the platform skill. Route-first; the resource model, tool routing, intent routing, preflight and execution rules live in `SKILL.md`, and everything else is a reference.
- `plugins/fly/skills/brand/SKILL.md`: Fly.io brand guidance from branding.fly.dev.

Sprites are one product reference inside `fly`, beside Machines, volumes and Managed Postgres. There is no separate Sprites skill.

## Reference loading pattern

1. Read `plugins/fly/skills/fly/SKILL.md`.
2. Choose the minimum reference set for the request.
3. For multi-step requests, load several references and compose one response.

| Intent | Reference |
|---|---|
| Install, sign in, tokens, MCP connection, agent tooling | `references/setup.md` |
| Create a new app | `references/launch.md` |
| Ship code or manage releases | `references/deploy.md` |
| Change configuration (`fly.toml`) | `references/configure.md` |
| Scale count, size, regions | `references/scale.md` |
| Individual Machines | `references/machines.md` |
| Volumes and snapshots | `references/volumes.md` |
| Secrets and environment | `references/secrets.md` |
| Networking, domains, certificates | `references/networking.md` |
| Postgres (managed and unmanaged) | `references/postgres.md` |
| Object storage, Redis, extensions | `references/storage.md` |
| Health, logs, access, troubleshooting | `references/operate.md` |
| Sprites | `references/sprites.md`, `references/sprites-cli.md` |
| MCP tool catalogue | `references/tools.md` |
| Safety rules | `references/safety.md` |

## Architecture

### Tool routing

- flyctl (`fly`): the complete surface, and the only path for anything touching the working directory, `fly.toml`, a shell on a Machine, deploys, IPs, certificates, Managed Postgres provisioning and partner services.
- Fly MCP (`https://mcp.fly.io`): OAuth-scoped, read-first access to existing apps, Machines, volumes, secret metadata, Managed Postgres and Sprites. The grant is per organization, app and product; `get_fly_context` reports it. The server does not create apps, deploy, change Machine configuration or administer organizations.
- Sprite CLIs: `sprite-env` inside a sprite, `sprite` outside. The MCP server exposes the same operations as tools.

### MCP

- Keep `plugins/fly/.mcp.json`, `plugins/fly/.cursor-plugin/mcp.json`, `plugins/fly/.grok-plugin/mcp.json` and `plugins/fly/mcp_config.json` (Antigravity's `serverUrl` schema) pointing at `https://mcp.fly.io` over HTTP.
- No credentials in plugin MCP config. Authentication is browser OAuth handled by the client.
- Tool names, constraints and the "not exposed" boundary are documented in `references/tools.md`; check it against `https://mcp.fly.io/guide.md` when the server changes.

## Authoring guidance

- Keep `SKILL.md` under 500 lines and the `description` at or under 1024 characters (the Agent Skills spec and Antigravity reject longer ones).
- Keep references action-oriented, one topic each, with flyctl commands shown exactly as the current binary accepts them. Verify flags against `fly <cmd> --help` and end each reference with a "Checked against" line.
- When a flyctl command and an MCP tool do the same thing, document both in the same reference, with the MCP constraints (grants, asynchronous results, what is not exposed) stated.
- Never put a secret value, token or example credential in a skill, reference, hook message or test fixture.
- Bump `version` in every `plugins/fly/.*-plugin/plugin.json` in any PR that changes skill content or plugin behaviour. CI checks that they agree.
- For Grok/xAI marketplace entries use the remote source subpath `plugins/fly` rather than root-level symlinks or copies.
- Run `python3 scripts/validate_skills.py` locally; CI runs it on every push and pull request.

## References

- https://agentskills.io/specification
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/plugins
- https://mcp.fly.io/guide.md
- https://fly.io/docs
