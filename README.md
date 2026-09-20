# {{PROJECT_NAME}}

> {{ONE_LINER — one sentence: what this is and who it's for}}

<!--
  This repository was created from Mont3-Suisse/template.
  First thing after cloning: run `/bootstrap` in Claude Code (or fill the {{...}}
  placeholders by hand) and delete these HTML comments.
  Keep this README in sync with reality — it is the front door of the project.
-->

## 📋 What it does

{{DESCRIPTION — 2–4 short paragraphs or a bullet list of the main features.}}

- {{feature 1}}
- {{feature 2}}
- {{feature 3}}

## 🧱 Stack

| Layer | Tech |
|---|---|
| Language / runtime | {{e.g. Python 3.12}} |
| Framework | {{e.g. Django 5 / static / Node}} |
| Data | {{e.g. SQLite → Postgres / none}} |
| Key services | {{e.g. Stripe, SendGrid, Anthropic}} |

## 🚀 Setup

Requirements: {{e.g. Python 3.12, git; Python on PATH is needed for the `.claude` hooks}}.

```bash
# 1. Clone
git clone git@github.com:Mont3-Suisse/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# 2. Configure environment
cp .env.example .env
#   → fill .env with the real values. NEVER commit .env.
#   → the real secret values live in Bitwarden (see PROJECT.md).

# 3. Install & run
{{install command, e.g. python -m venv .venv && pip install -r requirements.txt}}
{{run command, e.g. python manage.py runserver}}
```

## 💻 Usage

{{How to actually use the app once running — CLI commands, main URL, primary flow.}}

## 🗂️ Project structure

```
{{REPO_NAME}}/
├── {{...}}
└── {{...}}
```

## 📚 More docs

- **[PROJECT.md](PROJECT.md)** — operational handbook: deployment, environments, secrets, runbook.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how we work: branching, commits, PRs.
- **[CHANGELOG.md](CHANGELOG.md)** — what changed and when.
- **[CLAUDE.md](CLAUDE.md)** — conventions Claude Code follows in this repo.

---
<sub>Bootstrapped from [Mont3-Suisse/template](https://github.com/Mont3-Suisse/template).</sub>
