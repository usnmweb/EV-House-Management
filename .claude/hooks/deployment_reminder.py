#!/usr/bin/env python3
"""Stop hook: gentle, NON-BLOCKING reminder to keep deployment.json current.

If deploy-relevant files changed (Dockerfile, deploy/, systemd/nginx/caddy config,
dependency manifests, CI, settings, wsgi/asgi/gunicorn) but deployment.json wasn't
touched, print a one-line reminder. Always exits 0 (never blocks Claude from
stopping) and fails silently on any error.
"""
import sys
import subprocess

DEPLOY_HINTS = (
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
        deploy_changed = any(any(h in f.lower() for h in DEPLOY_HINTS) for f in files)
        manifest_touched = any(f.endswith("deployment.json") for f in files)
        if deploy_changed and not manifest_touched:
            sys.stderr.write(
                "Reminder: deploy-relevant files changed but deployment.json was not "
                "updated -- keep it in sync so the ops dashboard stays accurate.\n"
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
