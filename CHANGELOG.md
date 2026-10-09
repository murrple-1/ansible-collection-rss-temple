# Changelog

All notable changes to the `murrple_1.rss_temple` collection. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the collection follows
[Semantic Versioning](https://semver.org/).

## [2.0.0] - Unreleased

### Upgrading from 1.0.3

The playbooks never overwrite a config file that already exists: they save the new version next to it as
`<file>.<timestamp>` and print a notice. So most of the changes below only reach an existing server once the new
versions are merged in by hand, in each service directory.

- **Service directories:** the default service directories moved from `~/<name>/` to `/opt/rss_temple/<name>/`
  (`rss_temple_infra`, `rss_temple`, `rss_temple_web_app`, `rss_temple_home`). To keep using an existing deploy,
  set `pre_rss_temple__service_path`, `rss_temple__service_path`, `rss_temple_web_app__service_path` and
  `rss_temple_home__service_path` to the old `~/<name>/` paths, or move the directories. Otherwise the playbooks set
  up fresh directories, with newly generated passwords and secrets, as the same Compose projects (the project name
  comes from the directory name), and so on the same volumes. With PostgreSQL 18 that run fails at startup, because
  the 18 image refuses the old data volume.
- **Inventory and extra vars:** `rss_temple__postgres_local_data_directory` is renamed to
  `rss_temple__postgres_local_var_directory`, and is now mounted at `/var/lib/postgresql/` (see the PostgreSQL 18
  steps below). Install the collection's dependencies again (`ansible-galaxy collection install -r requirements.yml`),
  since it now needs `community.docker` 3.8.0 or later.
- **RSS Temple server version:** with this collection's default of `rss_temple__app_enable_silk: false`, the server
  must be **0.10.0 or later**. Every earlier server release crashes at startup with Silk disabled. To stay on an
  older server, set `rss_temple__app_enable_silk: true`.
- **`rss_temple/.env`:** add `POSTGRES_USER`, `POSTGRES_DB`, `APP_DB_NAME`, `APP_ENABLE_SILK` and
  `APP_CORS_ALLOWED_ORIGINS`. The new compose healthchecks read `POSTGRES_USER` and `POSTGRES_DB`.
- **`rss_temple/schedulerdaemon.json`:** add `"ignore_missed_top_images": {}`. Without it, the scheduler
  daemon of server 0.9.1 and later exits on startup and restarts in a loop.
- **`rss_temple/docker-compose.yml`:** merge in the PostgreSQL and Valkey healthchecks, the shared
  `depends_on`, and the `valkey_data` volume. Don't change the PostgreSQL image or volume path in the same step:
  see below.
- **`rss_temple/overrides/valkey.conf`:** add `appendonly yes` and `appendfsync everysec`.
- **`rss_temple/overrides/gunicorn.conf.py`:** add `preload_app = True` and the `on_starting` hook.
- **`rss_temple_web_app/Caddyfile`:** take the new `Content-Security-Policy` (its `connect-src` now comes from the
  API host), and drop `X-XSS-Protection` here and in `rss_temple_home/Caddyfile`.
- **Papertrail:** after the first `pre_rss_temple` run with Papertrail set up, remove the `logspout` service from
  `rss_temple_infra/docker-compose.yml` (otherwise logs reach Papertrail twice), then run
  `docker compose up --detach --force-recreate` in each service directory, so the containers pick up the new
  journald log driver.

#### PostgreSQL 17 to 18

New installs use `postgres:18-alpine`, with its data volume mounted at `/var/lib/postgresql/` (the layout the 18
image expects) instead of `/var/lib/postgresql/data/`. PostgreSQL 18 can't read a 17 data directory, so **don't just
change the image** of an existing server: dump the data, start 18 on an empty volume, and restore. Existing servers
keep running 17 until their `docker-compose.yml` is changed, so this can be done separately. In
`rss_temple/` (assuming the default `postgres` admin user and no service prefix):

1. Take a dump, and check it looks complete before going on:
   `docker compose exec -T postgresql pg_dumpall -U postgres > rss_temple.sql`
2. Stop the stack: `docker compose down`
3. Remove the old data volume (`docker volume ls` shows its name, `<project>_db_data`):
   `docker volume rm <project>_db_data`. With `rss_temple__postgres_local_var_directory`, point it at a new, empty
   directory instead.
4. In `docker-compose.yml`, change the image to `postgres:18-alpine` and the volume target to `/var/lib/postgresql/`.
5. Start PostgreSQL on its own: `docker compose up --detach --wait postgresql`
6. Restore: `docker compose exec -T postgresql psql -U postgres -d postgres < rss_temple.sql`. The errors
   `role "postgres" already exists` and `database "..." already exists` are expected.
7. Start the rest: `docker compose up --detach --wait`

Keep `rss_temple.sql` until the app is confirmed working.

### Added

- PostgreSQL and Valkey healthchecks. The app containers wait for both to be healthy, and the playbook waits for the
  whole stack (`docker compose up --wait`) instead of pausing for a fixed time.
- Valkey data (the Dramatiq job queue and caches) is persisted to a `valkey_data` volume, with the append-only file
  on (`rss_temple__valkey_appendonly`, default `true`).
- The `murrple_1.rss_temple.dotenv_quote` filter, which quotes values for a Docker Compose `.env` file.
- Server settings: `rss_temple__app_cors_allowed_origins` (prompted for; default `https://app.rsstemple.com`),
  `rss_temple__app_enable_silk` (default `false`) and the database name (`APP_DB_NAME`).
  `rss_temple_config.yml` now also prompts for the CSRF trusted origins.
- Gunicorn `preload_app`, with the server's URL resolver warm-up before forking, so the workers share the app's
  memory (`rss_temple__gunicorn_preload_app`, default `true`). With it, `kill -HUP` no longer reloads code: restart
  the container instead.
- `rss_temple_web_app__csp_extra_connect_src`, for extra `connect-src` sources in the web app's CSP.
- `pre_rss_temple__docker_group_user`, the user added to the `docker` group (default: `ansible_user`, or the
  connecting user).
- When a config file already exists and differs, the run prints where the new version was saved.
- A Development section in the README, on running the playbooks from a checkout.

### Changed

- **Breaking:** `rss_temple__postgres_local_data_directory` is renamed to `rss_temple__postgres_local_var_directory`.
- **Breaking:** new installs use PostgreSQL 18 (see the upgrade steps above).
- **Breaking:** the service directories moved to `/opt/rss_temple/<name>/` (see the upgrade steps above).
- **Breaking:** requires `community.docker` 3.8.0 or later, and declares its `community.general` and `ansible.posix`
  dependencies.
- The collection uses the standard layout: roles in `roles/`, the `django_secret` lookup in `plugins/lookup/`. The
  playbooks refer to roles and plugins by their full names (`murrple_1.rss_temple.<name>`), so run them by name
  (`ansible-playbook murrple_1.rss_temple.rss_temple`) from an installed collection.
- With Papertrail set up, container logs go to journald (tagged with the container name,
  `pre_rss_temple__docker_log_tag`) and from there through the host's rsyslog to Papertrail, instead of through
  `logspout`. The other settings in an existing `/etc/docker/daemon.json` are kept.
- Papertrail is optional: leave its host empty to skip it.
- Supported hosts are detected by OS family (Debian- or Red Hat-based), with a clear error on anything else.
- The Docker apt repository uses a `signed-by` keyring instead of the deprecated `apt_key`.
- The web app CSP's `connect-src` is derived from the API host, instead of a hard-coded `*.rsstemple.com`.
- Gunicorn workers are sized from the vCPU count, instead of the cores per socket.
- The app's Postgres user is created and configured in a single transaction, so a failure part-way no longer leaves
  a user without its grants.
- Facts are read through `ansible_facts[...]` throughout (ready for `INJECT_FACTS_AS_VARS=False`).
- Shared tasks (extras file, service directory) live in the `common` role.
- The "Unknown usage" prompts now describe the redirect URLs they set.
- Security defaults: config files get per-file modes, and the deploy user's shell profiles set `umask 027`.
- The service directories default to `/opt/rss_temple/<name>/` instead of the home directory, with a clear error
  when their parent isn't writable.
- CI lints the roles and playbooks, and publishes only for a tag matching `galaxy.yml`'s version, after lint passes.

### Fixed

- A `'` in a prompted value (such as a password) made Docker Compose reject the whole `.env` file, so the stack
  couldn't start. Values are now quoted for Compose instead of for a shell.
- `rss_temple_config.yml` failed because `overrides/` didn't exist yet.
- `local_settings.py` was written to the wrong service directory.
- The superuser was created with the unresolved `__rand__` placeholder instead of the generated password.
- Passwords passed to `psql` as arguments were shell-quoted, so their quotes became part of the password.
- A `'` in the app's Postgres password broke `CREATE USER`. The "user exists" check is also stricter, and retries
  while PostgreSQL starts.
- The scheduler daemon crash-looped: its config lacked the `ignore_missed_top_images` job.
- UFW was enabled before its allow rules were added, which could cut off the SSH connection.
- The `dnf` Docker repository step wasn't idempotent.
- The superuser email check rejected long TLDs and plus-addressing.
- Passwords and secrets were written to the extras files.
- rsyslog was restarted on every run, instead of only when its config changed.
- On local runs (`--connection=local`), the wrong user (or none) was added to the `docker` group.

### Removed

- The `logspout` container.
- The `X-XSS-Protection` header, which current browsers ignore.

## [1.0.3] - 2025-09-16

[2.0.0]: https://github.com/murrple-1/ansible-collection-rss-temple/compare/1.0.3...2.0.0
[1.0.3]: https://github.com/murrple-1/ansible-collection-rss-temple/releases/tag/1.0.3
