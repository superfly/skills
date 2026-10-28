# Fly.io Agent Skills

Agent skills and plugins for [Fly.io](https://fly.io): one `fly` skill that
covers the whole platform, packaged for every major coding agent, with the
hosted Fly MCP server bundled.

```bash
npx skills add superfly/skills
```

That installs the skill into any agent that supports the
[Agent Skills](https://agentskills.io) format (Claude Code, Codex, Cursor,
Gemini, Amp, OpenCode, Copilot and others). Re-run it to update.

## The `fly` skill

Lives at [`plugins/fly/skills/fly/SKILL.md`](plugins/fly/skills/fly/SKILL.md).
It is route-first: `SKILL.md` holds the resource model, the choice between
flyctl, the hosted MCP server and the Sprite CLIs, intent routing, preflight
and the execution rules. Everything else is a reference loaded on demand:

| Reference | Covers |
|---|---|
| `setup.md` | Install and upgrade flyctl, sign in and sign up, API tokens, connecting Fly MCP, installing these skills |
| `launch.md` | `fly launch`, `fly apps create`, the generated `fly.toml`, deploying an existing image |
| `deploy.md` | `fly deploy`, strategies, builders, release commands, verification, rollback |
| `configure.md` | The full `fly.toml` reference and `fly config` |
| `scale.md` | Machine count, VM size and memory, regions, autostop |
| `machines.md` | `fly machine` and the Machine MCP tools: lifecycle, exec, metadata, leases |
| `volumes.md` | Volumes, snapshots, mounts |
| `secrets.md` | `fly secrets`, staged secrets, build secrets |
| `networking.md` | IPs, certificates and custom domains, private networking, Flycast, WireGuard |
| `postgres.md` | Managed Postgres (`fly mpg` and MCP) and unmanaged `fly postgres` |
| `storage.md` | Tigris object storage, Upstash Redis, extensions |
| `operate.md` | Status, logs, SSH, console, troubleshooting playbooks |
| `sprites.md` | Sprites: persistent remote Linux environments, inside and outside, services, checkpoints, policy, gateway |
| `sprites-cli.md` | Every `sprite` and `sprite-env` command and the REST API |
| `tools.md` | The hosted Fly MCP tool catalogue |
| `safety.md` | Confirmation rules, recovery, what never to echo |

Sprites are documented as one Fly product beside Machines, volumes and
Managed Postgres, not as a separate skill.

## The `brand` skill

[`plugins/fly/skills/brand/`](plugins/fly/skills/brand/) teaches agents to
use the Fly.io brand from its source of truth,
[branding.fly.dev](https://branding.fly.dev): logos, colors and contrast,
typography, imagery, voice and naming, partner lockups and usage terms.

## Plugins and marketplaces

The same payload ships as a plugin for each agent, bundling the hosted MCP
server at `https://mcp.fly.io` (browser OAuth; the grant is per organization,
app and product) and, where the host supports hooks, a confirmation hook for
destructive, disruptive and billable operations.

| Agent | Install |
|---|---|
| Claude Code | `/plugin marketplace add superfly/skills` then `/plugin install fly@fly-skills` |
| Codex | Add this repository as a marketplace (`.agents/plugins/marketplace.json`) |
| Cursor | Add this repository as a plugin source (`.cursor-plugin/marketplace.json`) |
| Grok Build | xAI marketplace entry with source subpath `plugins/fly` |
| Google Antigravity | Install from the repository URL |

The hosted MCP server is also usable on its own in any MCP client:
connect `https://mcp.fly.io` as an HTTP server.

## Layout

```
plugins/fly/
  .claude-plugin/plugin.json      Claude Code manifest
  .codex-plugin/plugin.json       Codex manifest
  .cursor-plugin/                 Cursor manifest and mcp.json
  .antigravity-plugin/plugin.json Antigravity manifest (uses mcp_config.json)
  .grok-plugin/                   Grok manifest and mcp.json
  .mcp.json                       Hosted MCP server (Claude Code, Codex)
  hooks/hooks.json                PreToolUse confirmation hook
  scripts/fly_guard.py            The hook
  skills/fly/                     The skill: SKILL.md + references/
  skills/brand/                   Brand guidelines skill
.claude-plugin/marketplace.json   Claude Code marketplace
.cursor-plugin/marketplace.json   Cursor marketplace
.agents/plugins/marketplace.json  Codex marketplace
skills.sh.json                    Tells the skills.sh CLI where the skills live
scripts/validate_skills.py        Repository validator (run in CI)
```

The skills follow the [Agent Skills specification](https://agentskills.io/specification):
a directory holding a `SKILL.md` with `name` and `description` frontmatter,
references one level deep.

## Contributing

- Keep `SKILL.md` focused on routing, preflight, common operations and
  execution rules. Put detail in a reference.
- Each reference ends with a "Checked against" line naming the flyctl version
  or docs page it was verified against, and the date.
- Bump `version` in every `plugins/fly/.*-plugin/plugin.json` together when
  skill content or plugin behaviour changes; Claude Code uses it to detect
  updates.
- Run `python3 scripts/validate_skills.py` before opening a pull request.
  CI runs it too.

MIT licensed. Reviews route to `@superfly/agent-ecosystem`.
