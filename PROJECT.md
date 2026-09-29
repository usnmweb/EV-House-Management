# PROJECT — {{PROJECT_NAME}}

> **Operational handbook.** Everything needed to run, deploy and troubleshoot this project.
> ⚠️ **Secrets: names only, never values.** Real values live in **Bitwarden**
> (collection `{{BITWARDEN_COLLECTION}}`). Anyone committing a secret value must rotate it.

| | |
|---|---|
| **Owner** | {{@owner / team}} |
| **Status** | {{attivo (LIVE) / staging / dev / archived}} |
| **Last reviewed** | {{YYYY-MM-DD}} |
| **Repository** | https://github.com/Mont3-Suisse/{{REPO_NAME}} |
| **Production URL** | {{https://...}} |

## What it is

{{1–2 paragraphs: product, domain, purpose. Longer than the README one-liner.}}

## Stack & deployment

- **Stack**: {{language + framework + data store + notable libs}}
- **Host**: {{e.g. DigitalOcean VPS / Windows Server / mont3.ch / GitHub Actions}}
- **Process manager**: {{systemd unit `xxx.service` / NSSM service `xxx` / gunicorn / waitress}}
- **Ports**: {{app :8000, worker, reverse proxy}}
- **Reverse proxy**: {{Caddy / nginx — config path}}
- **Key directories on the server**: {{/opt/xxx, C:\apps\xxx}}

## Secrets (names only → Bitwarden)

| Variable | Purpose | Where used |
|---|---|---|
| `{{SECRET_NAME_1}}` | {{what it's for}} | {{service/module}} |
| `{{SECRET_NAME_2}}` | {{...}} | {{...}} |

> The canonical list of required variables is **[.env.example](.env.example)**.
> To rotate a secret: update Bitwarden → update the deployment env → redeploy.

## Environments

| Env | URL | Branch | Notes |
|---|---|---|---|
| Production | {{https://...}} | `main` | {{...}} |
| Staging | {{https://...}} | {{...}} | {{...}} |
| Local | http://localhost:{{port}} | any | uses `.env` |

## Deploy

- **How**: {{manual `git pull` + restart service / CI / rsync — describe the real procedure}}
- **Who can deploy**: {{roles}}
- **Steps**:
  ```bash
  {{deploy commands}}
  ```
- **Rollback**: {{how to revert — previous tag / snapshot / re-deploy prior commit}}

## Runbook

- **Restart**: `{{sudo systemctl restart xxx  /  nssm restart xxx}}`
- **Logs**: `{{journalctl -u xxx -f  /  path to log file}}`
- **Health check**: {{URL or command}}
- **Common issues**:
  - {{symptom → fix}}

## Security

- CI security scan: **[.github/workflows/security.yml](.github/workflows/security.yml)** → `Mont3-Suisse/security-ci`
  (gitleaks + osv-scanner + semgrep). Keep the `Security` check green.
- {{Any project-specific security notes: auth model, PII handling, data retention.}}
