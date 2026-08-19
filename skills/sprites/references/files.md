# Moving code and data

Ranked by reliability. Use the highest option that fits.

1. **`git clone` inside the sprite.** Fastest, gives the sprite a real
   repository, and skips every boundary problem below. Use it whenever the code
   is in a repository the sprite can reach.
2. **`sprite file push` / `sprite file pull`** for individual files from
   outside.
3. **The `fs` HTTP endpoints** (`PUT .../fs/write`, `GET .../fs/read`) when you
   are driving the API directly.
4. **A base64 payload decoded inside the sprite** for small generated files
   when nothing else is available.
5. **Ask the user** for an authorized transfer path for private code or
   secrets. Never invent credentials to get code in.

## Never sync

- `.git/` — clone or fetch inside the sprite instead of copying history.
- Dependency and build caches: `node_modules/`, `.venv/`, `target/`, `_build/`,
  `deps/`, `dist/`, `.next/`. Host artifacts are often built for a different
  platform. Reinstall in the sprite.
- Secrets: `.env` and variants, key files, certificates, token caches, cloud
  credential directories, shell history.
- Large datasets, media, and databases unless they are the actual payload and
  the user asked for them.
- Editor, OS, and agent state: `.DS_Store`, `.idea/`, local client config.

When a sync would carry a secret, stop and ask how the sprite should get it.
Supply credentials as service or exec environment values at run time rather
than writing them to the sprite's filesystem.

## Base64 pattern

Encode on the host, then decode in the sprite with separate arguments:

```bash
sprite exec -s dev -- python3 -c \
  "import base64,pathlib;pathlib.Path('/home/sprite/app/f').write_bytes(base64.b64decode('<B64>'))"
```

Create the parent directory first. Verify with `wc -c`, a checksum, or a small
targeted read. For several files, transfer one encoded archive and unpack it —
not a dozen fragile write commands.

## After transferring

Verify what actually landed with a file count, `du`, or a checksum before
building. Report which paths you copied and which you deliberately skipped, so
the user can correct the boundary.

Limit reads with `head`, `tail`, or `wc` before pulling a large file into model
context.
