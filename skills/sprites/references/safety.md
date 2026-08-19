# Safety

## Confirm before these

- Destroying a sprite.
- Restoring a checkpoint.
- Changing network, privilege, or resource policy in either direction.
- Making a URL public, or otherwise exposing a new HTTP surface.
- Stopping or killing services and sessions that the current task does not own.
- Broad destructive filesystem commands inside a sprite.

Resolve exact names and read current state before any of them. "The sprite that
looks unused" is not a resolved name.

## Do not confirm these

Creating a checkpoint. It is non-destructive, takes seconds, and asking wastes
the moment worth capturing. Take one before risky work and again when the user
says something works.

## Treat sprite URLs as public

Auth mode `sprite` limits access to organization members; `public` opens the
URL to the internet. Either way, a sprite service must never serve:

- environment dumps, tokens, API keys, or key files,
- arbitrary file browsing or upload endpoints,
- unfiltered logs,
- debug consoles, admin panels, or unauthenticated write endpoints,
- customer or personal data.

Switching a URL to `public` is a publication event. Confirm it, and say plainly
what becomes reachable.

## Policy updates replace the whole set

`POST .../policy/network` overwrites every rule. Read, merge, show the complete
intended set, confirm, write, then read back. The same applies to the
privileges and resources policies.

## Restore and destroy

Before a restore, name the target checkpoint with its comment and time, state
that every filesystem change after it is discarded, and offer to checkpoint the
current state first so the rollback itself is reversible. Verify the filesystem
and service state afterwards.

Destroying a sprite removes the environment, its services, its checkpoints, and
its URL. There is no undo and no soft-delete. State the exact target and the
impact before you run it.

## Secrets

- Prefer the API gateway or run-time environment values over credentials in
  files.
- Never place a token in a command argument, a log, a repository, a checkpoint,
  or served content.
- Never ask the user to paste a token into chat.
- A checkpoint captures the filesystem: a secret written to disk stays in every
  snapshot taken afterwards.

## Untrusted code

A sprite is a good place to run generated or untrusted code precisely because
it is isolated and snapshottable. Keep it that way: checkpoint first, leave the
network policy narrow, and do not mount host credentials into the environment
to make something work.
