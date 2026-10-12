# Public Release Gate

This checklist is intentionally conservative. A repository being technically accessible is not the same as being safe and ready for public release.

## Current blockers

- [ ] Repository visibility is still private; public visibility could not be changed through the available GitHub actions.
- [ ] `fly_state.json` is tracked on the existing `main` branch. Do not publish the repository until the maintainer decides how to remove runtime state from the public tree and whether history needs cleanup. Do not overwrite or reset the local state file during this audit.
- [ ] The repository root contains `fly-deploy-clean.zip`; its contents have not been audited for tokens, local state, or development-only files. Do not advertise it as a public release asset until it has been inspected/rebuilt.
- [ ] A standalone bot package was extracted into a fresh temporary directory and its dependencies installed; `import fly_bot` passed. Discord login failed with HTTP 401, so end-to-end runtime validation remains incomplete.
- [ ] Local packaging output exists outside this GitHub branch and has not yet been uploaded as a verified release asset.
- [ ] Run a complete secret scan of the full Git history before changing repository visibility. A current-file scan alone does not prove that credentials were never committed.

## Required before publishing

- [ ] Confirm no real credentials, personal data, or private runtime state exist in the public tree or history.
- [ ] Inspect every archive that will be downloadable.
- [ ] Decide which research/manuscript files are intended for public reading and check licensing/provenance for bundled assets.
- [ ] Verify fresh installation on a clean machine/environment.
- [ ] Verify Discord login, slash-command registration, dashboard delivery, asset paths, restart behavior, and state-file isolation.
- [ ] Run relevant tests and report exact scope/results.
- [ ] Add a release tag and attach only the clean, audited standalone bot archive.
- [ ] Change repository visibility only after the above blockers are resolved.

## What has been prepared on this branch

- Root project README with setup and research caveats.
- `.env.example` without credentials.
- `.gitignore` for local secrets, runtime state, caches, and release build output.

This checklist does not claim that a public release has occurred.
