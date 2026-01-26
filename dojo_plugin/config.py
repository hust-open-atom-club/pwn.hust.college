import warnings
import logging
import ast
import os
import pathlib
import json
import socket

from sqlalchemy.exc import IntegrityError
from CTFd.models import db, Admins, Pages
from CTFd.utils import config, set_config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DOJOS_DIR = pathlib.Path("/var/dojos")
DATA_DIR = pathlib.Path("/var/data")

KOOK_TOKEN = os.getenv("KOOK_TOKEN")
KOOK_GUILD_ID = os.getenv("KOOK_GUILD_ID")
KOOK_CLIENT_ID = os.getenv("KOOK_CLIENT_ID")
KOOK_CLIENT_SECRET = os.getenv("KOOK_CLIENT_SECRET")
KOOK_APP_ID = os.getenv("KOOK_APP_ID")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

def create_seccomp():
    seccomp = json.load(pathlib.Path("/etc/docker/seccomp.json").open())

    seccomp["syscalls"].append({
        "names": [
            "clone",
            "sethostname",
            "setns",
            "unshare",
        ],
        "action": "SCMP_ACT_ALLOW",
    })

    READ_IMPLIES_EXEC = 0x0400000
    ADDR_NO_RANDOMIZE = 0x0040000

    existing_personality_values = []
    for syscalls in seccomp["syscalls"]:
        if "personality" not in syscalls["names"]:
            continue
        if syscalls["action"] != "SCMP_ACT_ALLOW":
            continue
        assert len(syscalls["args"]) == 1
        arg = syscalls["args"][0]
        assert list(arg.keys()) == ["index", "value", "op"]
        assert arg["index"] == 0, arg
        assert arg["op"] == "SCMP_CMP_EQ"
        existing_personality_values.append(arg["value"])

    new_personality_values = []
    for new_flag in [READ_IMPLIES_EXEC, ADDR_NO_RANDOMIZE]:
        for value in [0, *existing_personality_values]:
            new_value = value | new_flag
            if new_value not in existing_personality_values:
                new_personality_values.append(new_value)
                existing_personality_values.append(new_value)

    for new_value in new_personality_values:
        seccomp["syscalls"].append({
            "names": ["personality"],
            "action": "SCMP_ACT_ALLOW",
            "args": [
                {
                    "index": 0,
                    "value": new_value,
                    "op": "SCMP_CMP_EQ",
                },
            ],
        })

    return json.dumps(seccomp)
SECCOMP = create_seccomp()

USER_FIREWALL_ALLOWED = {
    host: socket.gethostbyname(host)
    for host in pathlib.Path("/var/user_firewall.allowed").read_text().split()
}

DOJO_HOST = os.getenv("DOJO_HOST")
HOST_DATA_PATH = os.getenv("HOST_DATA_PATH")
BINARY_NINJA_API_KEY = os.getenv("BINARY_NINJA_API_KEY")
INTERNET_FOR_ALL = bool(ast.literal_eval(os.getenv("INTERNET_FOR_ALL") or "False"))

missing_errors = ["DOJO_HOST", "HOST_DATA_PATH"]
missing_warnings = ["BINARY_NINJA_API_KEY"]

for config_option in missing_errors:
    config_value = globals()[config_option]
    if not config_value:
        raise RuntimeError(f"Configuration Error: {config_option} must be set in the environment")

for config_option in missing_warnings:
    config_value = globals()[config_option]
    if not config_value:
        warnings.warn(f"Configuration Warning: {config_option} is not set in the environment")


def bootstrap():
    set_config("ctf_name", "pwn.hust.college")
    set_config("ctf_description", "pwn.hust.college")
    set_config("user_mode", "users")

    set_config("challenge_visibility", "public")
    set_config("registration_visibility", "public")
    set_config("score_visibility", "public")
    set_config("account_visibility", "public")

    set_config("ctf_theme", "dojo_theme")

    if not config.is_setup():
        admin = Admins(
            name="admin",
            email="admin@example.com",
            password="admin",
            type="admin",
            hidden=True,
        )
        try:
            db.session.add(admin)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        page = Pages(title=None, route="index", content="", draft=False)
        try:
            db.session.add(page)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        set_config("setup", True)

    db.session.commit()
