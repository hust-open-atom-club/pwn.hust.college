# AGENTS

This file provides guidance to AI coding agents when working with code in this repository.

## Overview

`pwn.hust.college` is a HUST-customized, independently maintained fork of the pwn.college DOJO platform. It is a CTFd-based cybersecurity training environment that runs inside an outer privileged Docker container named `dojo`. That outer container runs Docker-in-Docker and uses `docker-compose.yml` to start the platform services and per-user challenge workspaces.

This repository originated from upstream `pwncollege/dojo`. When behavior, architecture, or historical intent is unclear, it is acceptable to consult the upstream implementation for context, but treat this fork as the source of truth for current behavior.

The default development branch is `hustsec_dev`. Do not assume `master` or `main` is the target branch.

## Common Development Commands

Build and run the outer dojo container from the host:

```sh
docker build -t pwncollege/dojo .
docker run --privileged -d -v "$(pwd):/opt/pwn.college:shared" \
  -p 22:22 -p 80:80 -p 443:443 --name dojo pwncollege/dojo
docker exec dojo dojo logs
docker exec dojo dojo wait
```

Useful commands after the outer container is running:

```sh
docker exec dojo dojo sync
docker exec dojo dojo compose ps
docker exec dojo dojo compose logs -f
docker exec dojo dojo flask
docker exec dojo dojo db
docker exec dojo dojo enter [-s] <USER_ID|username>
docker exec dojo dojo backup
docker exec dojo dojo restore <path>
```

`dojo sync` copies `ctfd/*`, `dojo_plugin`, and `dojo_theme` into the running CTFd tree. Plugin and theme changes usually need only `dojo sync` and a CTFd restart. Changes under `ctfd/` or `challenge/` require a rebuild.

## Testing

The canonical integration harness is `test/local-tester.sh`:

```sh
sudo ./test/local-tester.sh
sudo ./test/local-tester.sh -T
sudo ./test/local-tester.sh -c my-dojo -D
MOZ_HEADLESS=1 pytest -v test/test_running.py
MOZ_HEADLESS=1 pytest -v test/test_running.py::test_login
CONTAINER_NAME=my-dojo pytest -v test/test_running.py
```

Tests talk to `http://localhost` and shell out through `docker exec <CONTAINER_NAME> dojo ...`. Run them on the host where the outer container is reachable, not inside the outer container.

Important test helpers:

- `test/utils.py::login`
- `test/utils.py::dojo_run`
- `test/utils.py::workspace_run`
- `test/utils.py::create_dojo`
- `test/utils.py::create_dojo_yml`
- `test/utils.py::make_dojo_official`
- `test/utils.py::generate_ssh_keypair`

`test/test_running.py` is the main platform integration suite. `test/test_discord_fixes.py` covers Discord-specific behavior.

## High-Level Architecture

### Outer Container

The root `Dockerfile` builds an Ubuntu 22.04 image, clones CTFd 3.6.0 into `/opt/CTFd`, installs Docker CE, copies this repository to `/opt/pwn.college`, and runs `dojo start`.

`dojo start` runs:

1. `dojo sync`
2. `dojo-init`
3. `systemd`

`systemd` starts `pwn.college.service`, which runs `docker compose up` using `docker-compose.yml`.

### Inner Services

The compose stack includes:

- `ctfd` - patched CTFd with `dojo_plugin` and `dojo_theme`
- `db` - MariaDB 10.4
- `cache` - Redis
- `sshd` - SSH entrypoint into running user containers
- `nginx` and `nginx-certs` - reverse proxy and ACME companion
- `prometheus`, `grafana`, and exporters - monitoring
- `challenge` - build target for the per-user challenge image

Containers share the `user_network` bridge (`10.114.0.0/16`). Per-user challenge containers are launched by the CTFd plugin through the host Docker socket mounted into `ctfd`.

### CTFd Plugin

`dojo_plugin` is the core application layer. Start reading at `dojo_plugin/__init__.py`.

Key areas:

- `dojo_plugin/pages/` - Flask blueprints for HTML views
- `dojo_plugin/api/v1/` - REST API mounted at `/pwncollege_api/v1`
- `dojo_plugin/models/` - SQLAlchemy models
- `dojo_plugin/utils/` - flag serialization, dojo loading, markdown, awards, workspace helpers
- `dojo_plugin/config.py` - env parsing, seccomp generation, CTFd bootstrap
- `dojo_plugin/prometheus_metrics.py` - request, solve, registration, and login metrics

The plugin registers `DojoChallenge` and `DojoFlag`. Flags are HMAC-signed per `(account_id, challenge_id)`. Do not add code paths that compare flags as plain strings.

HUST-specific integrations currently include HUST SSO, KOOK, Discord, course/grade workflows, and Prometheus/Grafana monitoring. SensAI/Open WebUI has been removed.

### Theme

`dojo_theme` is a full CTFd theme with Jinja templates, CSS, JavaScript, and images. It is bind-mounted read-only into the CTFd container. Edit theme files on the host, then run `dojo sync` and restart CTFd.

### Challenge Containers

When a user starts a challenge, `dojo_plugin/api/v1/docker.py` launches a per-user container from the image built by `challenge/Dockerfile_amd64` or `challenge/Dockerfile_arm64`.

Challenge containers:

- run as `hacker` UID 1000
- keep `/flag` readable only by root
- mount persistent home data from `data/homes`
- receive challenge files under `/challenge`
- use widened seccomp from `dojo_plugin/config.py::create_seccomp`
- auto-stop after `sleep 6h`

Outbound traffic is controlled by iptables rules from `dojo-init` and `user_firewall.allowed`.

### SSH Access

Port 22 reaches the `sshd` container. It looks up public keys in the CTFd database and `docker exec`s into the user's running challenge container.

## Configuration

Configuration flows through `data/config.env`. `dojo-init` is idempotent and only defines variables that are not already set.

Important variables:

- `DOJO_HOST`
- `HOST_DATA_PATH`
- `SECRET_KEY`
- `DOCKER_PSLR`
- `ARCH`
- `DOJO_ENV`
- `DOJO_CHALLENGE`
- `UBUNTU_VERSION`
- `INTERNET_FOR_ALL`
- `INSTALL_GDB`, `INSTALL_GHIDRA`, `INSTALL_RADARE2`, `INSTALL_KERNEL`, `INSTALL_DESKTOP`, and related tool flags
- `KOOK_*`
- `DISCORD_*`

`SECRET_KEY` signs user flags. Losing it invalidates existing user flags.

## Repository Conventions

- PRs normally target `hustsec_dev`.
- The plugin assumes CTFd 3.6.0. Do not bump it without auditing overridden CTFd view functions in `dojo_plugin/__init__.py`.
- `ctfd/0001-use-pycountry-to-replace-self-generated-country-list.patch` is applied at CTFd container startup. If it fails, CTFd will not boot.
- `dojo_plugin` and `dojo_theme` are mounted read-only into CTFd.
- `dojo-init` is safe to rerun.
- This fork is maintained independently, but upstream `pwncollege/dojo` can be used as a reference when local intent is ambiguous.
- Avoid unrelated refactors when changing platform behavior.
- Preserve HUST-specific behavior unless the task explicitly asks to remove it.

## Coding Standards

Prefer clear names and small functions over explanatory comments. Add comments only when they explain non-obvious why decisions, security constraints, or operational requirements.

Examples of useful comments:

```python
# SECRET_KEY signs user flags; rotating it invalidates all outstanding flags.
flag = serialize_user_flag(user.id, challenge.id)
```

Avoid comments that restate the next line of code.

When editing files:

- Use existing local patterns.
- Keep changes scoped to the requested behavior.
- Do not compare challenge flags as static strings.
- Do not remove HUST integrations opportunistically.
- Do not revert user changes unless explicitly asked.
