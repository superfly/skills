# Sprites Agent Skills

<!-- The skills.sh badge renders "resource not found" until the repository is
     public and indexed by the directory. Restore this line once it is:
[![skills.sh](https://skills.sh/b/superfly/skills)](https://skills.sh/superfly/skills)
-->

Agent Skills for [Sprites](https://sprites.dev) — isolated, persistent cloud
Linux environments from Fly.io, with their own filesystem, URL, services,
checkpoints, and network policy.

```bash
npx skills add superfly/skills
```

Install into any agent that supports the
[Agent Skills](https://www.skills.sh/docs) format: Claude Code, Codex, Cursor,
Gemini, Amp, and others.

## Why this repo

The skill works **from both sides of the boundary**:

- **Inside a sprite** — the agent is running in the environment it manages and
  drives the local `sprite-env` CLI over the sprite's API socket.
- **Outside a sprite** — the agent runs on a laptop, a CI runner, or another
  host, and drives sprites remotely with the `sprite` CLI or the REST API at
  `api.sprites.dev`.

It states which form applies and how to detect it, so an agent does not
burn a turn discovering that `sprite-env` is not installed or that `sprite -s`
is pointing at itself.

If your client speaks MCP, [`superfly/sprites-mcp`](https://github.com/superfly/sprites-mcp)
gives the same control plane as tools; this skill is the CLI/API path and
needs no MCP server.

## The skill

One skill, `sprites`, routes everything: detect the context, pick a control
plane, then follow the reference that matches the task. The references under
[`skills/sprites/references/`](skills/sprites/references/) cover:

| Reference | Use it for |
| --- | --- |
| `environment-detection.md` | Inside vs outside, installing either CLI, auth setup |
| `remote.md` | Create, list, target, exec into, copy files to, and destroy sprites from outside |
| `services.md` | Long-running processes and the public HTTP preview URL |
| `checkpoints.md` | Fast filesystem snapshots, rollback, and reading old files |
| `network-policy.md` | Outbound egress rules |
| `api-gateway.md` | Authenticated third-party APIs without handing the sprite a raw key |
| `cli.md` | The full `sprite-env` and `sprite` command surface |
| `http-api.md` | REST endpoints behind both CLIs, for agents with only an HTTP client |
| `files.md` | Moving code and data in and out |
| `safety.md` | Confirmation rules and exposure limits |

## Layout

```
skills/
  sprites/
    SKILL.md
    references/*.md
```

This is the standard skills.sh layout: a skill directory under `skills/`
holding a `SKILL.md` with `name` and `description` frontmatter.

## Contributing

Run the validator before opening a pull request:

```bash
python3 scripts/validate_skills.py
```

It checks frontmatter fields, name/directory agreement, description quality,
and relative links. The GitHub Actions workflow in `.github/workflows/ci.yml`
runs the same script on every push and pull request.

## License

MIT. See [LICENSE](LICENSE).
