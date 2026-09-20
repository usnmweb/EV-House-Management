# CLAUDE.md — {{PROJECT_NAME}}

Conventions for Claude Code in this repository. This file is loaded automatically every
session, so the project's rules travel with the repo — independent of who is working.

## What this project is
{{ONE_LINER}}. Full context in **[README.md](README.md)**; operations, deployment and secrets
in **[PROJECT.md](PROJECT.md)**; machine-readable deploy topology in **[deployment.json](deployment.json)**.

## Read first
Before non-trivial work, read: **README.md** (what/how), **PROJECT.md** (deploy, envs, secrets),
**CONTRIBUTING.md** (workflow). Prefer existing patterns and utilities over inventing new ones.

## Hard rules (do not violate)
1. **Never commit secrets.** `.env` and key material stay out of git. Real values live in
   **Bitwarden** (see PROJECT.md). Document new variables (name only) in `.env.example`.
   A `PreToolUse` hook blocks writing/adding `.env`/`*.pem`/`id_*`/`*.key` — do not work around it.
2. **Update the changelog.** For any user-facing change, add an entry under `[Unreleased]` in
   **CHANGELOG.md** in the same change (use `/changelog`).
3. **Conventional Commits.** `type(scope): subject`, imperative. Types: `feat fix docs refactor
   perf test build ci chore deploy`. Body explains *why* when non-obvious.
4. **Keep docs true.** If you change behaviour, deployment, env vars or structure, update the
   relevant doc (README/PROJECT/.env.example) in the same change.
5. **Keep `deployment.json` current.** It is the machine-readable deployment manifest the ops
   dashboard reads (which server, branch, path and service each project runs on). Whenever
   deployment topology changes — server, branch, path, service, port, domain or status — update
   `deployment.json` in the same change. A `Stop` hook reminds you when deploy-relevant files
   moved but the manifest didn't.

## Conventions
- Language for code, comments and docs: **English**.
- Match the surrounding code's style, naming and structure.
- Don't add dependencies without a reason; note new env vars in `.env.example` + PROJECT.md.
- Confirm before destructive or outward-facing actions (deploys, deletions, force-push).

## Commands
- `/bootstrap` — fill the `{{...}}` placeholders across README/PROJECT + `deployment.json` for a new project.
- `/changelog` — add an entry to `CHANGELOG.md` `[Unreleased]`.
- `/pr` — stage, write a Conventional Commit, and open a PR against `main`.

## Shared Mont3 skills
`mont3-toolkit` is declared in `.claude/settings.json` (`extraKnownMarketplaces` +
`enabledPlugins`), so the shared skills are available from the first session where this repo is
trusted. They trigger on their own, or are called by name:

- `mont3-footer` — the standard footer for client sites.
- `mont3-security-audit` — security and business-logic audit.
- `mont3-userflow-audit` — user-flow audit: every role, desktop and mobile.
- `mont3-consistency-audit` — visual and linguistic consistency, legal pages included.
- `mont3-timelogging` — log the hours worked on Francesca.

They live in **Mont3-Suisse/claude-plugins**. Improve them there, where every project gets the
change; never copy one into a project, or it stops being shared the moment it is copied.

## Project-specific notes
{{Add anything Claude should know: architecture quirks, gotchas, "always run X before Y",
test commands, local run command. Keep it current.}}
## Personal / local memory

Personal, per-project notes go in **`CLAUDE.local.md`** (git-ignored, imported below, never committed).
General personal preferences (all your projects) go in **`~/.claude/CLAUDE.md`**. Notes useful to the whole team belong in the "Project-specific notes" section above, added via PR.

@CLAUDE.local.md