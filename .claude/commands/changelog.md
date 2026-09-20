---
description: Add an entry to CHANGELOG.md [Unreleased]
argument-hint: [added|changed|deprecated|removed|fixed|security] <short description>
---
Add a [Keep a Changelog](https://keepachangelog.com/) entry under `[Unreleased]` in `CHANGELOG.md`.

- Category: from the first argument if given (Added/Changed/Deprecated/Removed/Fixed/Security);
  otherwise infer it from the current diff (`git diff` / `git diff --cached`).
- Text: from the remaining arguments, or summarize the current uncommitted changes into one
  concise, user-facing line.
- Do not duplicate an existing entry. Keep wording consistent with the existing changelog style.

Arguments: $ARGUMENTS
