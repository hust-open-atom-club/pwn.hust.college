#!/bin/sh

# adamd: hack here so that the auth.py command can get the environment variables we set in the docker compose
# Only propagate variables set by the compose config: dockerd injects process-state vars (HOME/PWD/SHLVL/HOSTNAME)
# into PID 1, and without filtering them pam_env applies HOME=/root to every SSH session, breaking tools that
# resolve the user's real home (e.g. docker CLI reading ~/.docker/config.json → "permission denied").
printenv | grep -v "no_proxy" | grep -vE "^(HOME|PWD|SHLVL|HOSTNAME)=" >> /etc/environment

/usr/sbin/sshd.pam -D -e -f /opt/sshd/sshd_config