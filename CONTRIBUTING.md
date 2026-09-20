# Contributing

How we work at **Mont3-Suisse**. These are shared **conventions** — not machine-enforced
gates (no forced branch protection or commit-lint by default). Follow them so any of us —
and Claude Code — can pick up any repo and feel at home. See **[CLAUDE.md](CLAUDE.md)** for
the machine-readable version Claude follows automatically.

## Branching (trunk-based)

- `main` is always deployable. Small, self-contained changes may go straight to it;
  open a PR when the change is worth a second pair of eyes, spans several files, or
  touches deployment. Some repos use a different trunk (`dev`, `staging`): the trunk
  is whichever branch `deployment.json` names, and that is the one that must stay
  deployable.
- Create short-lived branches off `main`:
  - `feature/<slug>` — new functionality
  - `fix/<slug>` — bug fixes
  - `chore/<slug>` — tooling, deps, housekeeping
  - `docs/<slug>` — documentation only
- Delete the branch after merge. Rebase on `main` to stay current; avoid long-lived branches.

## Commits — Conventional Commits

Format: `type(scope): subject` (imperative, lower-case, no trailing period).

```
feat(auth): add password reset flow
fix(search): handle empty query without 500
docs: document the deploy runbook in PROJECT.md
```

Types we use: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `deploy`.
Add a body (blank line, then bullets) to explain **why** when it isn't obvious. Reference issues
(`Closes #123`). Use `feat!:` / a `BREAKING CHANGE:` footer for breaking changes.

## Pull requests

- Keep them small and single-purpose. PR **title = a Conventional Commit line**.
- Fill in the PR checklist (`.github/PULL_REQUEST_TEMPLATE.md`): CHANGELOG updated, no secrets,
  tests where relevant.
- Ask for a review when the change is not obviously safe. Prefer **squash-merge** to
  keep the trunk linear. Nothing enforces a review: on private repositories under the
  organization's current GitHub plan, branch protection is not available.
- The **Security** check (gitleaks + osv-scanner + semgrep) should be green.

## Changelog

Update **[CHANGELOG.md](CHANGELOG.md)** `[Unreleased]` in the same PR as your change
(the `/changelog` command helps). Follow [Keep a Changelog](https://keepachangelog.com/).

## Versioning & releases

[Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`. On release, promote
`[Unreleased]` to the version + date and tag `vX.Y.Z`.

## Secrets — never commit them

- `.env` is git-ignored. Real values live in **Bitwarden** (see [PROJECT.md](PROJECT.md)).
- Document new variables (name only) in **[.env.example](.env.example)** and PROJECT.md.
- A committed `.claude` hook blocks Claude from writing/committing `.env` & key files;
  `gitleaks` (via CI) catches leaks in history. If a secret ever lands in a commit, **rotate it**.

## Optional: turn conventions into gates

By choice these are guidelines. To harden later:
- Require the `Security` check before merge — see the *"Enforcing the gate"* section of
  `Mont3-Suisse/security-ci`'s README.
- Branch protection and required reviews need a paid GitHub plan for private
  repositories. Until then the `Security` check is a signal, not a gate: read it.
