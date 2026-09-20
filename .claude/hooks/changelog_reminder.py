#!/usr/bin/env python3
"""Stop hook: gentle, NON-BLOCKING reminder to keep CHANGELOG.md current.

If the working tree has code changes but CHANGELOG.md wasn't touched, print a
one-line reminder. Always exits 0 (never blocks Claude from stopping) and fails
silently on any error.
"""
import sys
import subprocess


def changed_files():
    files = set()
    for args in (["git", "diff", "--name-only", "HEAD"],
                 ["git", "diff", "--cached", "--name-only"]):
        try:
            out = subprocess.run(args, capture_output=True, text=True, timeout=5)
            files.update(l.strip() for l in out.stdout.splitlines() if l.strip())
        except Exception:
            pass
    return files


def main():
    try:
        files = changed_files()
        if not files:
            return
        code_changed = any(not f.endswith(".md") for f in files)
        changelog_touched = any(f.endswith("CHANGELOG.md") for f in files)
        if code_changed and not changelog_touched:
            sys.stderr.write(
                "Reminder: code changed but CHANGELOG.md [Unreleased] was not updated "
                "-- consider running /changelog.\n"
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
