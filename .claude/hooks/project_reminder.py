#!/usr/bin/env python3
"""Stop hook: gentle, NON-BLOCKING reminder to keep PROJECT.md current.

PROJECT.md is the operational handbook (stack, deployment, secrets, runbook).
If files that make it stale changed -- deploy/infra config, dependency
manifests, the env template (.env.example), or app settings -- but PROJECT.md
wasn't touched, print a one-line reminder. Always exits 0 (never blocks Claude
from stopping) and fails silently on any error.
"""
import sys
import subprocess

# changes that usually mean PROJECT.md (stack / deploy / secrets / runbook) is now stale
DOC_HINTS = (
    ".env.example", ".env.sample",            # a new/removed secret -> secrets table
    "dockerfile", "docker-compose", "deploy/", ".service", "nginx", "caddyfile",
    "requirements", "package.json", "pyproject", "procfile", "gunicorn",
    "wsgi", "asgi", ".github/workflows/", "settings",
)


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
        relevant = any(any(h in f.lower() for h in DOC_HINTS) for f in files)
        project_touched = any(f.endswith("PROJECT.md") for f in files)
        if relevant and not project_touched:
            sys.stderr.write(
                "Reminder: stack/deploy/env files changed but PROJECT.md was not "
                "updated -- refresh the handbook (stack, deploy, secrets, runbook).\n"
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
