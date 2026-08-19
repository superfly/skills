# Sprites Agent Skills

[![skills.sh](https://skills.sh/b/superfly/sprites-skills)](https://skills.sh/superfly/sprites-skills)

Agent Skills for [Sprites](https://sprites.dev) — isolated, persistent cloud
Linux environments from Fly.io, with their own filesystem, URL, services,
checkpoints, and network policy.

```bash
npx skills add superfly/sprites-skills
```

Install into any agent that supports the
[Agent Skills](https://www.skills.sh/docs) format: Claude Code, Codex, Cursor,
Gemini, Amp, and others.

## Why this repo

These skills work **from both sides of the boundary**:

- **Inside a sprite** — the agent is running in the environment it manages and
  drives the local `sprite-env` CLI over the sprite's API socket.
- **Outside a sprite** — the agent runs on a laptop, a CI runner, or another
  host, and drives sprites remotely with the `sprite` CLI or the REST API at
  `api.sprites.dev`.

Every skill states which form applies and how to detect it, so an agent does not
burn a turn discovering that `sprite-env` is not installed or that `sprite -s`
is pointing at itself.

If your client speaks MCP, [`superfly/sprites-mcp`](https://github.com/superfly/sprites-mcp)
gives the same control plane as tools; these skills are the CLI/API path and
need no MCP server.

## Skills

| Skill | Use it for |
| --- | --- |
| `sprites` | Entry point: detect the context, pick a control plane, core model and safety rules |
| `sprites-remote` | Create, list, target, exec into, copy files to, and destroy sprites from outside |
| `sprites-services` | Long-running processes and the public HTTP preview URL |
| `sprites-checkpoints` | Fast filesystem snapshots, rollback, and reading old files |
| `sprites-network-policy` | Outbound egress rules |
| `sprites-api-gateway` | Authenticated third-party APIs without handing the sprite a raw key |

`sprites` carries deeper references under
[`skills/sprites/references/`](skills/sprites/references/): environment
detection, the full CLI surface, the HTTP API, file transfer, and safety.

## Layout

```
skills/
  sprites/
    SKILL.md
    references/*.md
  sprites-remote/SKILL.md
  sprites-services/SKILL.md
  sprites-checkpoints/SKILL.md
  sprites-network-policy/SKILL.md
  sprites-api-gateway/SKILL.md
```

This is the standard skills.sh layout: one directory per skill under `skills/`,
each holding a `SKILL.md` with `name` and `description` frontmatter.

## Contributing

Run the validator before opening a pull request:

```bash
python3 scripts/validate_skills.py
```

It checks frontmatter fields, name/directory agreement, description quality,
and relative links. CI runs the same script.

## License

MIT. See [LICENSE](LICENSE).
