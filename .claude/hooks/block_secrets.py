#!/usr/bin/env python3
"""PreToolUse guard for Mont3-Suisse repos.

Blocks Claude from writing, editing, or git-staging/committing secret files
(.env, *.pem, *.key, id_rsa/id_ed25519, service-account*.json, ...).

Design principle: FAIL OPEN. Any parsing/runtime error exits 0 (allow), so a
misconfigured environment never blocks normal work. It only blocks on a clear
secret match (exit code 2 = block, reason printed to stderr).
"""
import sys
import os
import re
import json

SECRET_BASENAMES = {".env", "credentials.json"}
SECRET_PATTERNS = [
    r"^\.env($|\.)",                 # .env, .env.local, .env.production, ...
    r"\.pem$", r"\.key$", r"\.pfx$", r"\.p12$",
    r"^id_(rsa|ed25519|ecdsa|dsa)$",
    r"_(rsa|ed25519)$",
    r"^service-account.*\.json$",
]
ALLOW_BASENAMES = {".env.example", ".env.sample"}


def is_secret(path):
    if not path:
        return False
    base = os.path.basename(str(path).strip().strip('"').strip("'"))
    if base in ALLOW_BASENAMES:
        return False
    if base in SECRET_BASENAMES:
        return True
    return any(re.search(p, base) for p in SECRET_PATTERNS)


def bash_touches_secret(cmd):
    if not cmd:
        return False
    # Only guard commands that would put files into git.
    if not re.search(r"\bgit\s+(add|commit|stash)\b", cmd):
        return False
    for tok in re.split(r"\s+", cmd):
        if is_secret(tok):
            return True
    # Force-adding an otherwise-ignored secret.
    if re.search(r"\bgit\s+add\b.*\b(-f|--force)\b", cmd) and \
       re.search(r"\.env|\.pem|\.key|id_(rsa|ed25519)", cmd):
        return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    hit = False
    if tool in ("Write", "Edit", "MultiEdit"):
        hit = is_secret(tool_input.get("file_path", ""))
    elif tool == "Bash":
        hit = bash_touches_secret(tool_input.get("command", ""))

    if hit:
        sys.stderr.write(
            "BLOCKED by .claude secrets guard: this targets a secret/key file "
            "(.env, *.pem, *.key, id_*, service-account*.json).\n"
            "Secrets never go in git -- real values live in Bitwarden (see PROJECT.md). "
            "Document only the variable NAME in .env.example.\n"
        )
        sys.exit(2)  # block the tool call

    sys.exit(0)


if __name__ == "__main__":
    main()
