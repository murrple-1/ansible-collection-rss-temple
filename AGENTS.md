# AGENTS.md — ansible-collection-rss-temple (deployment)

Ansible collection `murrple_1.rss_temple` that deploys RSS Temple, a self-hostable RSS/Atom reader, onto a
single Debian- or RedHat-family host with Docker Compose. It is one of four repos; see
[Sibling repositories](#sibling-repositories) for the others and when to read them.

## Layout

- `roles/pre_rss_temple/` — host preparation: packages, firewall (ufw or firewalld), optional Papertrail, and
  the "infra" Caddy that fronts every domain. Service dir: `/opt/rss_temple/rss_temple_infra/`.
- `roles/rss_temple/` — backend: `murraychristopherson/rss_temple` image plus Postgres, Valkey and a Caddy.
  Templates: `.env.j2` (all `APP_*` settings), `docker-compose.yml.j2`, `Caddyfile.j2`,
  `gunicorn.conf.py.j2`, `schedulerdaemon.json.j2`, `valkey.conf.j2`.
- `roles/rss_temple_web_app/` — `murraychristopherson/rss_temple_web_app`. Templates `config.json`
  (the web app's runtime config), `Caddyfile` and `index.head.html`.
- `roles/rss_temple_home/` — `murraychristopherson/rss_temple_home` landing site. Templates `.env` and
  `*.head.html`; ships static `contact.html`, `tos.html`, `privacy.html`.
- `roles/common/` — shared task files (`safe_file_overwrite`, `safe_template_overwrite`, `service_dir`, …).
- `playbooks/` — one playbook per role, plus a `*_config.yml` variant that only writes config.
  All use `hosts: all`; there is no inventory in the repo.
- `plugins/lookup/django_secret.py`, `plugins/filter/dotenv_quote.py`.

## How it works

- Variables are named `<role>__<name>`, for example `rss_temple__app_allowed_hosts`. Most are collected
  with `vars_prompt` in the playbooks.
- A secret prompt left at `__rand__` is generated and stored in
  `playbooks/_credentials/<var>.<inventory_hostname>.password` (git-ignored). Never commit or print those files.
- **The playbooks never overwrite an existing config file.** They write the new version next to it as
  `<file>.<timestamp>` and print a notice. Any template change that matters to existing servers needs an
  "Upgrading from X" section in `CHANGELOG.md` telling operators what to merge by hand.

## Commands

```sh
ansible-galaxy collection install -r requirements.yml
ansible-lint . roles/ playbooks/       # what CI runs (ansible-lint 25.9.0)
pre-commit run --all-files

# Playbooks refer to roles by collection name, so install the working copy first:
ansible-galaxy collection install . --force
ansible-playbook --connection=local --inventory localhost, murrple_1.rss_temple.rss_temple
```

There is no molecule and there are no tests. CI is CircleCI (`.circleci/config.yml`): lint on every push. On
tags it checks that the tag equals `version` in `galaxy.yml`, then builds and publishes to Galaxy.

## Conventions

- `CHANGELOG.md` follows Keep a Changelog and SemVer, with an "Upgrading from X" subsection for manual steps.
- Keep `galaxy.yml` `version` in step with the release tag.
- Write config files with the `common` role's `safe_template_overwrite` / `safe_file_overwrite` tasks, not with
  a bare `template` or `copy`. They keep the "never overwrite an existing config" behaviour.
- Name new variables `<role>__<name>`, give them a default in `roles/<role>/defaults/main.yml` or a prompt in
  the playbook, and quote values that go into a `.env` file with the `dotenv_quote` filter.

## Definition of done

1. `ansible-lint . roles/ playbooks/` passes.
2. `pre-commit run --all-files` passes.
3. A changed template renders: run the matching `*_config.yml` playbook against a scratch or local host, or at
   least `ansible-playbook --syntax-check`.
4. `CHANGELOG.md` has an entry under `[Unreleased]`. If existing servers need a config merged by hand, add it to
   the "Upgrading from X" subsection.
5. Any new `APP_*` variable exists in the backend's `settings.py` (see below).

## Do not

- Run a playbook against a real host, or anything that changes a remote server, without the user's explicit
  go-ahead. These playbooks deploy production.
- Read, print or commit anything in `playbooks/_credentials/`, `*.password` or `*.django_secret` files, or a
  generated `.env`. They hold live secrets.
- Put a real secret in a default or a prompt default. Use `__rand__` or leave it empty.
- Create git tags or bump `galaxy.yml` `version` unless asked. A tag publishes to Ansible Galaxy.

## Security notes

- The firewall tasks in `roles/pre_rss_temple/` open only SSH, 80 and 443. Keep it that way. The internal
  services (Postgres, Valkey, the per-app Caddies) must stay on Docker networks and must not publish host ports.
- `APP_NUM_PROXIES` must equal the number of proxies in front of gunicorn: the infra Caddy plus the backend's
  Caddy, so 2. The backend Caddyfile trusts `X-Forwarded-For` only from private ranges. If you change either,
  clients can spoof their IP and get around rate limits.
- No task uses `no_log` yet. If you add a task whose output would show a secret (for example a `debug` or a
  `command` that echoes one), add `no_log: true`.

## Sibling repositories

RSS Temple is split across four repos, normally checked out side by side. Local paths are relative to this
repo's root. If a sibling is not checked out, use its GitHub URL (for example with `gh`).

| Repo | Local path | GitHub | What it provides |
| --- | --- | --- | --- |
| Backend | `../rss_temple` | https://github.com/murrple-1/rss_temple | Django API, workers, scheduler, `rss_temple` image |
| Frontend | `../rss_temple_ui` | https://github.com/murrple-1/rss_temple_ui | Angular web app and Eleventy landing site, `rss_temple_web_app` and `rss_temple_home` images |
| Deployment (this repo) | `.` | https://github.com/murrple-1/ansible-collection-rss-temple | Ansible collection `murrple_1.rss_temple` that deploys all images on one server |
| Infrastructure | `../terraform-rss-temple` | https://github.com/murrple-1/terraform-rss-temple | Terraform for the Linode server and firewall |

The images this collection deploys are built and pushed to Docker Hub by the backend and frontend repos'
CircleCI (`:latest` from `master`, `:<tag>` from git tags). The `*__docker_version` variables pick the tag.

### When to read them from here

- **What an `APP_*` setting means, its default, or whether it exists** — `../rss_temple/rss_temple/settings.py`
  (every setting is an `os.getenv("APP_…")`). `../rss_temple/.env.example.dev` documents most of them.
  Before adding a line to `roles/rss_temple/templates/.env.j2`, confirm the backend reads it.
- **Backend process commands** (gunicorn, Dramatiq, scheduler daemon, migrations) — the dev compose files in
  `../rss_temple` (`docker-compose.yml`, `docker-compose.override.dev.yml`), `gunicorn.conf.py` and
  `schedulerdaemon.example.json`. The backend `README.md` has a full production compose and Caddyfile that
  this collection should agree with.
- **Release upgrade steps** — `../rss_temple/CHANGELOG.md` "Upgrading from X" sections, often mirrored here.
- **Postgres backups and major upgrades** — `../rss_temple/DB.md`.
- **Web app `config.json` keys** — the zod schema in
  `../rss_temple_ui/rss-temple-web-app/src/app/services/config.service.ts` decides what
  `roles/rss_temple_web_app/templates/config.json.j2` must contain. The dev example is
  `../rss_temple_ui/rss-temple-web-app/src/assets/config.json`.
- **Home env vars** — `../rss_temple_ui/rss-temple-home/` (`.eleventy.js`, `Dockerfile`).
- **Frontend URLs in backend settings** (email verify, password reset, social) must match routes in
  `../rss_temple_ui/rss-temple-web-app/src/app/app.routing.ts`.
- **The target host** (OS image, size, open ports 22/80/443) — `../terraform-rss-temple`. Nothing feeds
  Terraform outputs into an inventory automatically; the server IP is passed by hand.
