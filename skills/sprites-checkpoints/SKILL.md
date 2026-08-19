---
name: sprites-checkpoints
description: Use this skill to snapshot and roll back a Sprite's filesystem. Trigger it before risky work (package upgrades, migrations, bulk edits, untrusted code), after a change is confirmed working, and for any request to save, snapshot, roll back, restore, or undo the environment. Checkpoints are copy-on-write and take seconds, so take them often.
license: MIT
metadata:
  author: Fly.io
  version: "1.0.0"
---

# Sprites checkpoints

A checkpoint is a point-in-time snapshot of the sprite's writable filesystem
overlay. Creating one is cheap and fast. Restoring one rewinds the environment
and discards everything written after the snapshot.

Checkpoints are versioned `v0`, `v1`, `v2`, … The last five are mounted read-only
at `/.sprite/checkpoints/` inside the sprite, so you can read an old file
without restoring anything.

## Commands

| Action | Inside a sprite | Outside a sprite |
| --- | --- | --- |
| Create | `sprite-env checkpoints create --comment "<why>"` | `sprite checkpoint create -s <name>` |
| List | `sprite-env checkpoints list` | `sprite checkpoint list -s <name>` |
| Inspect | `sprite-env checkpoints get v3` | `sprite checkpoint info v3 -s <name>` |
| Restore | `sprite-env checkpoints restore v3` | `sprite restore v3 -s <name>` |

`sprite-env checkpoints list --history <version>` filters by environment
version.

## When to create one

Create a checkpoint:

- Before package upgrades, database migrations, bulk rewrites, or bulk deletes.
- Before running generated or untrusted code.
- Before a network-policy or service-definition change.
- **Whenever the user says something works, looks right, or is done.** That is
  the state worth keeping, and it is easy to lose.
- At any point you would want to come back to.

Always pass `--comment`. Write the reason, not the action:
`--comment "before node 22 upgrade"`, `--comment "auth flow passing tests"`.
A list of unlabelled checkpoints is close to useless a day later.

Do not ask permission to create a checkpoint. It is non-destructive, it takes
seconds, and the cost of skipping one is much higher than the cost of taking it.

## Restoring

Restore is destructive to current state. Before running it:

1. List checkpoints and name the exact target, with its comment and time.
2. Tell the user plainly that every filesystem change made after that
   checkpoint is discarded, including uncommitted work and installed packages.
3. Offer to create a checkpoint of the current state first, so the rollback is
   itself reversible.
4. Get explicit approval.

Restore returns immediately and triggers an asynchronous restore that restarts
the environment. Sessions drop. After it completes, verify the filesystem and
check that services came back with `sprite-env services list`.

## Reading an old file without restoring

Prefer this over a restore whenever the user needs one file or a diff:

```bash
ls /.sprite/checkpoints/
diff /.sprite/checkpoints/v3/home/sprite/app/config.toml /home/sprite/app/config.toml
```

Only the five most recent checkpoints are mounted.

## Limits

- Only the writable overlay is captured. Content from the base image is not
  part of the snapshot, and neither is state held outside the sprite.
- Individual checkpoints cannot be deleted. Destroying the sprite removes all
  of them.
- Checkpoints are not a backup of an external database, and they are not a
  substitute for committing and pushing code.
