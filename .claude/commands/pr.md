---
description: Stage, commit (Conventional Commits) and open a PR against main
allowed-tools: Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git checkout:*), Bash(git status:*), Bash(git diff:*), Bash(gh pr create:*), Bash(gh pr view:*)
---
Prepare a pull request following Mont3-Suisse conventions (see CONTRIBUTING.md):

1. `git status` + `git diff` to review changes. Confirm no secrets/`.env` are staged.
2. If still on `main`, create a branch off it: `feature/*`, `fix/*`, `chore/*`, or `docs/*`.
3. Ensure `CHANGELOG.md [Unreleased]` covers the change (run `/changelog` if missing).
4. Stage and commit with a Conventional Commit: `type(scope): subject`, plus a short body
   explaining *why* when non-obvious.
5. Push the branch and open the PR with `gh pr create` — title = the commit subject,
   body = summary + the checklist from the PR template.
6. Print the PR URL.

Pause and ask me before pushing if anything looks off.
