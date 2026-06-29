# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`pwn.hust.college` is a HUST-customized fork of the [pwn.college DOJO](https://github.com/pwncollege/dojo) platform: a CTFd-based cybersecurity training environment. The whole platform runs inside an "outer" privileged Docker container ("dojo" container) that itself runs docker-in-docker to launch per-user challenge workspaces.

Default working branch is `hustsec_dev` (not `master`/`main`). Docs live in `docs/`; the most important are `architecture.md`, `general_deployment.md`, and `challenge.md`.

## Architecture

### Everything runs inside the `dojo` container

`Dockerfile` (root) builds an Ubuntu 22.04 image that clones CTFd 3.6.0 into `/opt/CTFd`, clones `sensai` (the AI-TA fork of Open WebUI) into `/opt/sensai`, installs Docker CE inside, and copies this repo to `/opt/pwn.college`. `CMD ["dojo", "start"]` runs `dojo sync`, then `dojo-init`, then `systemd`, which drives `pwn.college.service` (a `docker compose up` defined in `docker-compose.yml`).

Inner compose stack: `ctfd` (the patched CTFd), `db` (mariadb 10.4), `cache` (redis), `sshd`, `nginx` (nginxproxy/nginx-proxy + acme-companion), `open-webui` (sensai), `prometheus`, `grafana`, plus node/mysql/redis/nginx exporters. Containers share a custom `user_network` bridge (`10.114.0.0/16`), and per-user challenge containers are launched onto the same network by the plugin via the host Docker socket that is bind-mounted into `ctfd`.

`dojo-init` runs before systemd and is **idempotent** — it only defines config variables that aren't already set, so it's safe to re-run:
- Seeds `data/config.env` with defaults for required variables: `DOJO_HOST`, `DOJO_ENV`, `DOJO_CHALLENGE`, `SECRET_KEY` (auto-generated HMAC key for flag signing), `ARCH` (auto-detected), `INTERNET_FOR_ALL`, and tool install flags (`INSTALL_GDB`, `INSTALL_GHIDRA`, …)
- Creates a 1 GB `homes/homefs` loopback ext4 image for per-user persistent home directories
- Sets up `iptables` rules for the user firewall from `user_firewall.allowed`
- Generates `/etc/docker/seccomp.json` with widened syscalls (see `config.py::create_seccomp`)
- `data/config.env` is sourced by everything downstream: `docker-compose.yml`, the `dojo` dispatcher, and `dojo-init` itself on subsequent runs

### CTFd integration model — `dojo_plugin` + `dojo_theme`

The platform is implemented as a **CTFd plugin** mounted read-only at `/opt/CTFd/CTFd/plugins/dojo_plugin` and a **CTFd theme** mounted at `/opt/CTFd/CTFd/themes/dojo_theme`. Start reading at `dojo_plugin/__init__.py`:

- Registers a `DojoChallenge` class and a `DojoFlag` class. Flags are HMAC-signed per `(account_id, challenge_id)` — see `DojoFlag.compare` and `utils.unserialize_user_flag`. There is no static flag table; users get personal flags.
- Overrides several CTFd view functions (`views.static_html`, `views.settings`, `challenges.listing`) and deletes the built-in scoreboard/users blueprints — the plugin replaces them entirely.
- Registers blueprints for: `dojos`, `dojo`, `workspace`, `desktop`, `sso` (HUST SSO), `users`, `course`, `writeups`, `belts`, `kook`, `discord`, `sensai`, plus the REST API blueprint at `/pwncollege_api/v1`.
- Wraps WSGI with `DispatcherMiddleware` to expose `/metrics` for Prometheus. `prometheus_metrics.py` adds request/solve/login counters.
- Patches CTFd email (adds `Date` header) and adds a `hidden` field to `UserSchema`.
- `dojo_plugin/config.py` calls `bootstrap()` on load: hardcodes `ctf_name`, `user_mode=users`, sets `ctf_theme=dojo_theme`, and creates an `admin/admin` admin on first run. **Change the admin password after first deploy.**

The plugin follows a layered structure:
- `pages/` — Flask blueprints for HTML views (dojos, workspace, desktop, sso, kook, discord, sensai, course, writeups, belts, users, settings, index)
- `api/v1/` — REST API blueprint at `/pwncollege_api/v1` (`docker.py` starts challenge containers, `scoreboard.py`, `belts.py`, `dojo.py`, `discord.py`, `sso_login.py`, …)
- `utils/` — business logic: flag serialization (`serialize_user_flag`/`unserialize_user_flag`), markdown rendering, dojo loading (`load_dojo`), firewall, seccomp, award tracking, IP addressing
- `models/` — SQLAlchemy models: `Dojos`, `DojoChallenges`, `Belts`, `Emojis`, `DojoMembers`, `DojoAdmins`
- `config.py` — bootstrap + env-var parsing (reads from docker-compose environment)
- `scripts/warm_cache.py` — cache warming
- `prometheus_metrics.py` — Prometheus counters (request/solve/login)

### `dojo_theme`

The theme at `dojo_theme/` is a full CTFd theme with `templates/` (Jinja2 HTML) and `static/` (CSS/JS/images). It is bind-mounted read-only into the ctfd container alongside the plugin. Edit theme files, then `dojo sync` and restart ctfd — no rebuild needed.

HUST-specific surface vs upstream pwncollege/dojo: `pages/sso_login.py` (HUST SSO), `pages/kook.py` + `utils/kook.py` (KOOK chat), `pages/discord.py` + `utils/discord.py` (Discord), `pages/sensai.py` (AI TA via Open WebUI), `prometheus_metrics.py`, plus the `monitoring/` Prometheus/Grafana stack. Many features are env-var gated via `docker-compose.yml` — absent credentials mean those integrations are inert.

### Per-user challenge containers

When a user starts a challenge, the plugin launches a container from the image built by `challenge/` (`Dockerfile_amd64` / `Dockerfile_arm64`, target `challenge-final`, sized by `DOJO_CHALLENGE` = `challenge-nano`|`micro`|`mini`|`full`). The challenge container:

- Runs as `hacker` UID 1000, with `/flag` readable only by root.
- Has challenge binaries at `/challenge/` as root-owned setuid programs — users exploit them to read `/flag`.
- Mounts the user's persistent home from the `homes/homefs` loopback image (1 GB per user, set up by `dojo-init`).
- Has seccomp widened by `dojo_plugin/config.py::create_seccomp` at bootstrap (allows `clone`, `setns`, `unshare`, `sethostname`, plus specific `personality()` flags for `READ_IMPLIES_EXEC`/`ADDR_NO_RANDOMIZE`).
- Auto-stops after `sleep 6h`.

Outbound traffic from user containers is firewalled by `iptables` rules set in `dojo-init` (allowlist in `user_firewall.allowed`, plus explicit ACCEPT for the sensai container at `10.114.0.11`).

The `challenge/` directory builds this image. Key contents:
- `Dockerfile_amd64` / `Dockerfile_arm64` — multi-stage build (`challenge-base` → `challenge-slim` → `challenge-final`), gated by `DOJO_CHALLENGE` and `INSTALL_*` build args
- `docker-entrypoint.sh` / `docker-initialize.sh` — container startup scripts
- `services.d/` — s6 service definitions for VNC, noVNC, SSH, etc.
- `desktop/` — XFCE desktop environment files
- `vm/` — virtual machine integration
- `setuid_interpreter.c` — compiled setuid binary that executes challenge binaries as root (so `/flag` stays root-readable only)
- `bash.bashrc` — custom bashrc for the `hacker` user

### Access paths

- **HTTP**: `nginx-proxy` → CTFd → plugin starts/attaches to user container on demand.
- **SSH**: port 22 hits the `sshd` container, which looks the public key up in the CTFd DB and `docker exec`s into the user's running container.

## Commands

All `dojo` subcommands come from `dojo/dojo` (bash dispatcher) and run **inside the outer `dojo` container**. Invoke them as `docker exec dojo dojo <subcommand>` from the host, or directly inside the container.

### Build & run the outer container (from host)

```sh
docker build -t pwncollege/dojo .
docker run --privileged -d -v "$(pwd):/opt/pwn.college:shared" \
  -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
docker exec dojo dojo logs                                       # watch startup (first run builds challenge image, slow)
docker exec dojo dojo wait                                       # block until compose finishes coming up
```

Defaults: listens on `localhost.pwn.hust.college` (resolves to 127.0.0.1), `DOJO_ENV=development`, `DOJO_CHALLENGE=challenge-mini`. Override with `-e KEY=value` on `docker run` or by editing `data/config.env` after first boot. `DOJO_CHALLENGE=challenge-full` is ~70 GB.

### `dojo` subcommands (inside outer container)

- `dojo start` — entrypoint: runs `dojo sync` then `dojo-init` then `exec /usr/bin/systemd`.
- `dojo sync` — copies `ctfd/*` → `/opt/CTFd/`, `dojo_plugin` → `/opt/CTFd/CTFd/plugins/`, `dojo_theme` → `/opt/CTFd/CTFd/themes/`. Run after editing plugin/theme code without a full rebuild.
- `dojo update` — `git pull && dojo sync && dojo compose up -d --build`. Only safe when you understand every incoming commit; otherwise do the full rebuild flow in `docs/general_deployment.md`.
- `dojo compose <args>` — `docker compose` with `--env-file=/opt/pwn.college/data/config.env`.
- `dojo flask` — `flask shell` in the ctfd container. The shell context processor (`dojo_plugin/__init__.py::shell_context_processor`) pre-imports both `CTFd.models` and `dojo_plugin.models`.
- `dojo db` — `mysql` client against the ctfd database.
- `dojo enter [-s] <USER_ID|username>` — `docker exec` into a user's running challenge container. `-s` enters as root.
- `dojo backup` / `dojo restore <path>` — dump/restore the mariadb to/from `data/backups/`.
- `dojo logs` — `journalctl -u pwn.college -f`.

### Tests

`test/local-tester.sh` is the canonical integration harness. It kills/rebuilds a `dojo-test` container, waits for startup, optionally restores a backup, and runs `pytest -v test/test_running.py`.

```sh
sudo ./test/local-tester.sh                       # rebuild + run full suite
sudo ./test/local-tester.sh -T                    # rebuild + skip tests
sudo ./test/local-tester.sh -c my-dojo -D         # custom container name, blank data volume
MOZ_HEADLESS=1 pytest -v test/test_running.py     # run tests against an already-running container
MOZ_HEADLESS=1 pytest -v test/test_running.py::test_login    # single test
CONTAINER_NAME=my-dojo pytest ...                 # point tests at non-default container
```

Tests talk to `http://localhost` and shell out via `docker exec <CONTAINER_NAME> dojo ...` (see `test/utils.py::dojo_run`). They need to run on the host where the outer container is reachable, not inside it. Browser-based tests require `MOZ_HEADLESS=1`.

Key test helpers in [test/utils.py](test/utils.py):
- `login(name, password, *, register=False)` — creates an authenticated `requests.Session` with CSRF token
- `dojo_run(*args)` — runs `docker exec <CONTAINER_NAME> dojo ...` from the host
- `workspace_run(cmd, *, user, root=False)` — runs a command inside a user's challenge container
- `create_dojo(repo_type, repo, *, session)` / `create_dojo_yml(spec, *, session)` — creates dojos via the REST API
- `make_dojo_official(dojo_rid, admin_session)` — promotes a dojo to official
- `generate_ssh_keypair()` — generates an ed25519 keypair for dojo creation

Pytest fixtures in [test/conftest.py](test/conftest.py):
- `admin_session` (session-scoped) — authenticated admin session (admin/admin)
- `random_user` (function-scoped) — fresh random user per test; auto-registers
- `completionist_user` / `guest_dojo_admin` (session-scoped) — persistent test users
- `example_dojo` (session-scoped) — the `hust-open-atom-club/example-dojo` repo loaded as an official dojo
- `simple_award_dojo` (session-scoped) — a dojo loaded from `test/dojos/simple_award_dojo.yml`

Test dojo YAML specs live in `test/dojos/` — these are loaded as fixtures by `create_dojo`/`create_dojo_yml`. `test_discord_fixes.py` contains Discord-specific tests separate from the main suite.

## Conventions

- Config flows through `data/config.env`. `dojo-init` is idempotent: it only defines variables that aren't already set, so you can pre-seed the file or pass `-e` to `docker run`.
  - **Required**: `DOJO_HOST` (e.g. `localhost.pwn.hust.college`), `HOST_DATA_PATH`
  - **Auto-generated**: `SECRET_KEY` (HMAC key for flag signing — losing it invalidates all user flags), `DOCKER_PSLR` (Docker TLS key), `ARCH` (auto-detected from `dpkg --print-architecture`)
  - **Sizing**: `DOJO_CHALLENGE` (`challenge-nano`|`micro`|`mini`|`full` — controls which tools are baked into the challenge image), `DOJO_ENV` (`development` uses Flask dev server; anything else uses gunicorn), `UBUNTU_VERSION` (default `22.04`)
  - **Network**: `INTERNET_FOR_ALL` (`True`/`False` — controls outbound network access for user containers)
  - **Tool flags**: `INSTALL_GDB`, `INSTALL_GHIDRA`, `INSTALL_RADARE2`, `INSTALL_KERNEL`, `INSTALL_DESKTOP`, etc. — all default to `no` except `INSTALL_DESKTOP=yes`
  - **Integrations**: `KOOK_*` (KOOK chat), `DISCORD_*` (Discord), `OLLAMA_BASE_URLS` / `OPENAI_API_BASE_URL` (sensai AI TA) — absent credentials make these integrations inert
- `dojo_plugin` and `dojo_theme` are **bind-mounted read-only** into the ctfd container (`docker-compose.yml`). Edit files on the host, then `dojo sync` (or restart ctfd) — no rebuild needed for plugin/theme-only changes. Changes under `ctfd/` or `challenge/` do require rebuild (`dojo compose up -d --build`).
- The `dojo/dojo` bash dispatcher is a simple `case` statement over `$ACTION` (`start`, `sync`, `update`, `compose`, `flask`, `db`, `enter`, `backup`, `restore`, `logs`, `wait`). It sources `data/config.env` at startup and shells out to `docker exec`.
- The plugin assumes CTFd 3.6.0 pinned in `Dockerfile` (`--branch 3.6.0`); do not bump without auditing `dojo_plugin/__init__.py` for removed/renamed CTFd view functions.
- Challenge IDs and flags are opaque per-user signed tokens — never add code paths that compare flags as plain strings.
- `ctfd/0001-use-pycountry-to-replace-self-generated-country-list.patch` is applied to CTFd at container start; if it fails to apply, CTFd won't boot (see the `command:` block in `docker-compose.yml`).
- PRs normally target `hustsec_dev`. See `CONTRIBUTING.md`.
