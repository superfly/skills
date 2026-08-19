---
name: sprites-network-policy
description: Use this skill when outbound network access from a Sprite is blocked, or when the user wants to allow, deny, or audit which domains a sprite can reach. Trigger it for DNS or egress errors during package installs, git operations, or API calls from a sprite, and for any request to change the sprite's network policy. The update replaces the entire rule set, so read before you write.
license: MIT
metadata:
  author: Fly.io
  version: "1.0.0"
---

# Sprite network policy

A sprite's outbound traffic is filtered by a DNS-based allow/deny list. Code in
the sprite can reach the domains the policy permits and nothing else. This is
what makes a sprite safe to run untrusted or agent-generated code in.

## Read first — always

```bash
# Inside a sprite (read-only by design)
curl -s --unix-socket /.sprite/api.sock http://sprite/policy/network

# Outside a sprite
sprite api "/v1/sprites/<name>/policy/network"
```

The response is `{"rules": [{"domain": ..., "action": "allow"|"deny",
"include": ...}]}`. A rule may carry `include` naming a preset bundle, such as
`{"include": "defaults"}`, instead of a single domain.

Writing the policy from inside the sprite is deliberately impossible — the
local socket exposes `GET /policy/network` only, so code running in the sprite
cannot widen its own egress. Changes go through the remote API or the MCP tool
`policy_network_update`.

## Update replaces, it does not merge

```bash
sprite api "/v1/sprites/<name>/policy/network" -- \
  -X POST -H "Content-Type: application/json" \
  -d '{"rules":[{"include":"defaults"},{"domain":"registry.npmjs.org","action":"allow"}]}'
```

`POST` overwrites the whole rule set. Sending one new rule silently deletes
every existing rule. The procedure is always:

1. Read the current rules.
2. Build the complete intended set from them, adding or removing one entry.
3. Show the user the full resulting set and get approval.
4. Write it.
5. Read it back and confirm what landed.

Widening egress is a security decision, not a build fix. Confirm before adding
a domain, and add the narrowest domain that unblocks the work rather than a
wildcard.

## Diagnosing a block

Egress denial usually surfaces as a DNS failure or a hung connection, not as a
clear "blocked" message. Before changing anything:

1. Reproduce with a single command inside the sprite:
   `curl -sS -o /dev/null -w '%{http_code}\n' https://<host>/`.
2. Read the current policy and check whether the exact host is covered. A rule
   for `example.com` does not necessarily cover `cdn.example.com`.
3. Resolve the hostname the tool actually contacts — package managers and
   installers often use a different CDN host than their main site.

Do not work around the policy by using a raw IP address. Policy is DNS-based,
IPs move, and a hard-coded address hides the real dependency from whoever reads
the policy later.

## Related surfaces

Two sibling policies exist on the same path prefix and follow the same
read-modify-write rule: `/v1/sprites/<name>/policy/privileges` for capability
and device restrictions, and `/v1/sprites/<name>/policy/resources` for memory
limits. Treat both as security-relevant and confirm before changing them.

If the goal is to call a third-party API rather than to reach a general host,
prefer the gateway — see the `sprites-api-gateway` skill. It needs no policy
change and keeps the credential out of the sprite.
