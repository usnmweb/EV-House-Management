# Deploying the website

The EV House website is a Django app (Django 5.2, Python 3.12, gunicorn, WhiteNoise, SQLite).
Everything it needs on its server was prepared on 2026-09-28, and **a deploy is one command**:

```bash
sudo /usr/local/sbin/evhouse-deploy
```

Nothing is served yet: until the code is in this repository, that command answers "Nothing to
deploy yet". [First deploy](#first-deploy) says how to bring it here. This directory holds the
files the box needs besides the code, each byte-identical to the installed copy: the systemd unit,
the deploy script, the `evhouse-manage` helper and the nginx site.

It follows the scheme of the Blue Venado demo on the same box (`Mont3-Suisse/blue-venado-website`,
`deploy/README.md`): a checkout owned by a service account, a build under a memory cap, and people
who deploy with their own account and never as root. There is no CI deploy.

## Where it runs

| | |
|---|---|
| Host | DigitalOcean droplet `24.199.86.139` ("server 2"), Ubuntu 24.04, 4 GB, Python 3.12. It also runs Francesca, the Blue Venado demo, content.mont3.ch and scanandfly.com |
| URL | `https://evhouse.mont3.dev/`, a **preview** (see below). DNS: an A record in the `mont3.dev` zone, on GoDaddy |
| Checkout | `/srv/evhouse/app`, a clone of `main` |
| Virtualenv | `/srv/evhouse/venv`, created by the first deploy |
| Data | `/srv/evhouse/data/db/db.sqlite3` (mode 700 directory) and `/srv/evhouse/data/media/` (the photos), outside the checkout. Database copies before every deploy in `/srv/evhouse/data/db/backups/`, the last 15 |
| Settings | `/srv/evhouse/evhouse.env`, owned by `evhouse`, mode 600, never in git: `DJANGO_SECRET_KEY` (generated on the box), `DJANGO_DEBUG=False`, hosts, CSRF origin, database and media paths; SMTP and the admin user optional |
| Owner of all of it, and of the process | `evhouse` (uid and gid 951), a system user with no shell and no password |
| Unit | `evhouse-website.service` ([evhouse-website.service](evhouse-website.service)): gunicorn on `127.0.0.1:3300`, 2 workers, `MemoryMax=512M`. Enabled, but skipped until the code and the virtualenv exist |
| Deploy | `/usr/local/sbin/evhouse-deploy` ([evhouse-deploy](evhouse-deploy)), run through sudo |
| Django commands | `/usr/local/bin/evhouse-manage` ([evhouse-manage](evhouse-manage)), run as evhouse |
| Proxy | its own nginx site, `/etc/nginx/sites-available/evhouse.mont3.dev` ([nginx-evhouse.mont3.dev.conf](nginx-evhouse.mont3.dev.conf)): `/media/` straight from disk, everything else to gunicorn (static files are WhiteNoise's), uploads up to 25 MB, TLS from Let's Encrypt through certbot |
| Logs | `journalctl -u evhouse-website`, and this site's own `/var/log/nginx/evhouse.access.log` and `evhouse.error.log` |
| GitHub access | a read-only deploy key in `/srv/evhouse/.ssh/github_deploy`, registered on this repository as "server2 24.199.86.139 /srv/evhouse (read-only)" |

**It is a preview, not EV House's production site** (evhousemanagement.com). nginx sends
`X-Robots-Tag: noindex, nofollow` on every response and answers `/robots.txt` with a disallow of
its own, whatever the app says. When the site moves to the client's domain, that is a new
`server_name` and certificate, those two nginx lines removed, and `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` changed in the settings file.

**The app forces HTTPS** when `DJANGO_DEBUG` is off (`config/settings.py`: redirect, secure
cookies, HSTS for a year with preload) and trusts `X-Forwarded-Proto`, which nginx sends. So a
request straight to gunicorn without that header answers 301: test it with
`curl -H 'Host: evhouse.mont3.dev' -H 'X-Forwarded-Proto: https' http://127.0.0.1:3300/`.

- **The service belongs to no person.** People log in with their own account and use
  `sudo -u evhouse` for anything in `/srv/evhouse`. Never run `git`, `pip` or `manage.py` as root
  there: root-owned files break the next deploy.
- **The box can read the repository but cannot write to it.** Nothing is ever committed from the
  server, and `evhouse-deploy` refuses to run over local edits.
- **The commit that is live is a fact, not a guess:**
  `sudo -u evhouse -H git -C /srv/evhouse/app log --oneline -1`.

## Who can deploy

People log in with a personal account, by key only, with no password. They do not become root;
they act on the application through its service account.

| | |
|---|---|
| Group `devteam` | the personal accounts of the people who work on applications on this box. `/etc/sudoers.d/devteam` lets them run anything **as a member of `appsvc`**, never as root: `sudo -u evhouse -H git log`, `sudo -u evhouse nano /srv/evhouse/evhouse.env`, `sudo -u evhouse evhouse-manage createsuperuser` |
| Group `appsvc` | the service accounts: `blue-venado`, `evhouse` |
| Deploy and restart | reserved to root or to a pipeline. Until this project has a pipeline, a temporary, named exception (`/etc/sudoers.d/alberto-deroga-evhouse`) lets the `alberto` account run exactly `/usr/local/sbin/evhouse-deploy` and `systemctl restart evhouse-website`, nothing else. It goes at the first deploy from a pipeline, or on 2026-10-31 |
| Logs | the same account reads this site's logs only, through fixed commands (`/etc/sudoers.d/alberto-log-evhouse`): `sudo journalctl -u evhouse-website --no-pager -n 200` (or `-f`), and `sudo tail -n 200` (or `-f`) of the two `evhouse.*.log` files. Nobody outside the admins reads the journal or the nginx logs in general: the box runs Francesca, whose logs carry client data |

`evhouse-deploy` takes no arguments, so whoever runs it through sudo cannot change what it does,
and everything in it that touches code or data runs as `evhouse`. This whole path was exercised
end to end on 2026-09-28 with the `alberto` account, over SSH.

## First deploy

1. **Bring the code into this repository.** On 2026-09-28 it lives in `usnmweb/EV-House-Management`
   (a personal, public repository). From a clone of it:
   ```bash
   git remote add mont3 git@github.com:Mont3-Suisse/evhouse-website.git
   git fetch mont3
   git merge --allow-unrelated-histories mont3/main     # keep your README.md; keep deploy/, deployment.json, .github/, CLAUDE.md
   git push mont3 HEAD:main
   ```
   A merge, not a force-push: `deploy/` and `deployment.json` must stay. From then on this is the
   repository to work in.
2. **Deploy:** `sudo /usr/local/sbin/evhouse-deploy`. The first run creates the virtualenv and
   downloads the property photos: about two to four minutes.
3. **The admin user:** `sudo -u evhouse evhouse-manage createsuperuser` (or the
   `DJANGO_SUPERUSER_*` lines in the settings file, which `build.sh` reads on the next deploy).
4. **The manifest:** move the entry prepared under `pending_topology_change` in `deployment.json`
   into `deployments[]`, with `status` set to `dev`. The ops dashboard reads that file from `main`.

## Every deploy

Push to `main`, then on the server:

```bash
sudo /usr/local/sbin/evhouse-deploy
```

It does, in order, and stops at the first error:

1. **Code**: fetches and fast-forwards the checkout to `origin/main`, as `evhouse`. It refuses if
   the checkout is not on `main` or has local edits.
2. **Database backup**: copies the SQLite database (the `sqlite3` backup API, consistent while the
   site runs) to `/srv/evhouse/data/db/backups/db-<time>-<previous commit>.sqlite3`, keeping 15.
3. **Build**: runs the repository's own `build.sh` (the steps Render runs: `pip install`,
   `collectstatic`, `migrate`, the admin user, the property import, the display names, the blog
   covers) as `evhouse`, with the settings file, inside a transient unit capped at 1.6 GB of
   memory. **One app build at a time on this box**: it shares a lock with Blue Venado's build
   (`/run/lock/app-build.lock`); "Another build is running on this box" means wait and run it
   again. If the build fails the site is not restarted and keeps running the previous version.
4. **Restart** of `evhouse-website`.
5. **Check**: the home page must answer 200 within 30 seconds; if not, it prints the last log lines
   and exits with an error.

`sudo systemctl restart evhouse-website` alone is for a settings change: edit
`/srv/evhouse/evhouse.env` as `evhouse`, then restart.

## Rollback

- **The code**: revert the commit on GitHub (`git revert`), push, deploy.
- **The database too**, when the bad deploy carried a migration: revert the code on GitHub first,
  then put back the copy that deploy took (named after the commit it replaced), then deploy. The
  copy goes back through the same SQLite backup API, so the site does not need to be stopped:
  ```bash
  sudo -u evhouse python3 -c 'import sqlite3, sys; s, d = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2]); s.backup(d); d.close()' \
    /srv/evhouse/data/db/backups/db-<time>-<commit>.sqlite3 /srv/evhouse/data/db/db.sqlite3
  sudo /usr/local/sbin/evhouse-deploy
  ```
  The backups live on the same disk: they cover a bad deploy, not a lost server.

## Setting it up on a new box

What was done on server 2 on 2026-09-28, in order; nothing in it touched the other sites. The
groups `devteam` and `appsvc`, and `/etc/sudoers.d/devteam` (`%devteam ALL=(%appsvc) NOPASSWD:
ALL`), already existed for Blue Venado.

```bash
# 1. The service account. System user, no shell, no password, home in /srv.
sudo groupadd --system -g 951 evhouse
sudo useradd --system -u 951 -g 951 -G appsvc --shell /usr/sbin/nologin --home-dir /srv/evhouse --no-create-home evhouse
sudo install -d -m 755 -o evhouse -g evhouse /srv/evhouse /srv/evhouse/data /srv/evhouse/data/media
sudo install -d -m 700 -o evhouse -g evhouse /srv/evhouse/data/db /srv/evhouse/data/db/backups

# 2. The deploy key. Generated on the box; the private half never leaves it.
sudo install -d -m 700 -o evhouse -g evhouse /srv/evhouse/.ssh
sudo -u evhouse -H ssh-keygen -t ed25519 -N "" -C "evhouse-website@server2 24.199.86.139 (read-only deploy key)" -f /srv/evhouse/.ssh/github_deploy
printf 'Host github.com\n    IdentityFile ~/.ssh/github_deploy\n    IdentitiesOnly yes\n' | sudo -u evhouse -H tee /srv/evhouse/.ssh/config >/dev/null
#    known_hosts: github.com's host keys, checked against https://api.github.com/meta.
#    Then, from a machine with gh, register the PUBLIC half, read-only:
#    gh repo deploy-key add github_deploy.pub --repo Mont3-Suisse/evhouse-website --title "server2 24.199.86.139 /srv/evhouse (read-only)"
sudo -u evhouse -H ssh -T git@github.com     # "successfully authenticated"

# 3. The checkout.
sudo -u evhouse -H git clone -b main git@github.com:Mont3-Suisse/evhouse-website.git /srv/evhouse/app

# 4. The settings file, mode 600, owned by evhouse, with a secret key generated on the box:
#    DJANGO_SECRET_KEY, DJANGO_DEBUG=False, DJANGO_ALLOWED_HOSTS=evhouse.mont3.dev,
#    DJANGO_CSRF_TRUSTED_ORIGINS=https://evhouse.mont3.dev,
#    DJANGO_DB_PATH=/srv/evhouse/data/db/db.sqlite3, DJANGO_MEDIA_ROOT=/srv/evhouse/data/media
#    (python3 -c 'import secrets; print(secrets.token_urlsafe(50))' for the key).

# 5. The scripts and the unit, from this directory. The unit is enabled at once: it is skipped
#    until the code and the virtualenv exist, so it cannot fail in a loop.
sudo install -m 755 deploy/evhouse-deploy /usr/local/sbin/evhouse-deploy
sudo install -m 755 deploy/evhouse-manage /usr/local/bin/evhouse-manage
sudo install -m 644 deploy/evhouse-website.service /etc/systemd/system/evhouse-website.service
sudo systemctl daemon-reload && sudo systemctl enable evhouse-website

# 6. nginx and the certificate. The site file here is the FINAL one, certbot's lines included,
#    and nginx refuses it until the certificate exists: install its first server block only, with
#    `listen 80;` in place of the five lines marked "managed by Certbot", link it, reload; once the
#    DNS record answers:
sudo ln -s /etc/nginx/sites-available/evhouse.mont3.dev /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d evhouse.mont3.dev --redirect
#    certbot adds its five lines and a port-80 block of its own, built on the request's Host
#    variable: replace that block with the last one in deploy/nginx-evhouse.mont3.dev.conf, then
#    diff the two files.

# 7. The collaborator's rights: /etc/sudoers.d/alberto-deroga-evhouse and alberto-log-evhouse,
#    mode 440, each checked with `sudo visudo -cf`.
```

`nginx -t` first, every time: a syntax error takes down every site on the box, Francesca included.

## Checked before the first deploy

On 2026-09-28, `usnmweb/EV-House-Management` at `dc27309` was deployed on the box in an isolated
copy, with this unit's settings, then deleted: `build.sh` ran in 137 s (528 photos, 88 MB, a
780 KB database); the home page, `/properties/`, `/blog/`, `/admin/login/`, `robots.txt`
and `sitemap.xml` answered 200, `/giornale/` 301 to `/blog/`, an unknown page 404; the 14 static
files of the home page 200; gunicorn used 82 MB.

## Known limits

- **The build shares the box with Francesca.** The cap and the shared lock make the build die
  first and never run twice at once, but for the minutes it runs it competes for CPU and network.
- **The database backups are on the same disk**, and the box has no off-site copy of `/srv/evhouse`.
- **There is no health check of this unit's own.** The Mont3 ops agent on the box asks the ops
  dashboard what runs here, and the dashboard reads `deployment.json` from `main`: keep it true.
