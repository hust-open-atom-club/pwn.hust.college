import os
from enum import Enum
from logging import getLogger

import requests
from flask import url_for
from CTFd.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_BOT_TOKEN, DISCORD_GUILD_ID


OAUTH_AUTHORIZE_ENDPOINT = "https://discord.com/oauth2/authorize"
OAUTH_TOKEN_ENDPOINT = "https://discord.com/api/oauth2/token"
API_ENDPOINT = "https://discord.com/api/v9"

# Retry transient connection-level failures (e.g. connection reset by peer
# when the path to Discord is intermittently blocked) - 3 attempts, 0.5/1/2s backoff.
# 429/5xx are intentionally NOT retried: 429 keeps the original drop semantics,
# and non-idempotent replay risk is accepted since a reset means the request
# almost certainly never reached Discord.
_session = requests.Session()
_session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.5,
    allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "HEAD"]),
)))


class DiscordChannels(Enum):
    AWARD = os.getenv("DISCORD_CHANNEL_ID_AWARD")
    WELCOME = os.getenv("DISCORD_CHANNEL_ID_WELCOME")
    NOTIFICATION = os.getenv("DISCORD_CHANNEL_ID_NOTIFICATION")


def discord_request(endpoint, method="GET", **kwargs):
    logger = getLogger(__name__)
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    response = _session.request(method, f"{API_ENDPOINT}{endpoint}", headers=headers, **kwargs)
    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 1)
        logger.warning(f"Discord rate limited on {method} {endpoint}, retry_after={retry_after}s. Dropping request.")
        return None
    response.raise_for_status()
    if "application/json" in response.headers.get("Content-Type", ""):
        return response.json()
    else:
        return response.content


def guild_request(endpoint, method="GET", **kwargs):
    return discord_request(f"/guilds/{DISCORD_GUILD_ID}{endpoint}", method=method, **kwargs)


def discord_avatar_asset(discord_member):
    if not discord_member:
        return url_for("views.themes", path="img/dojo/discord_logo.svg")
    discord_id = discord_member["user"]["id"]
    discord_avatar = discord_member["user"]["avatar"]
    return f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"


def get_discord_id(auth_code):
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": url_for("discord.discord_redirect", _external=True),
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = _session.post(OAUTH_TOKEN_ENDPOINT, data=data, headers=headers, timeout=10)
    access_token = response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = _session.get(f"{API_ENDPOINT}/users/@me", headers=headers, timeout=10)
    discord_id = response.json()["id"]
    return discord_id


def get_discord_member(discord_id):
    # Only successful lookups are cached (1h): a transient network failure
    # must NOT pin "no member" for an hour, or the settings page would keep
    # showing a bare Discord ID until the cache expires.
    if not DISCORD_BOT_TOKEN or not discord_id:
        return
    member = cache.get(f"discord_member:{discord_id}")
    if member is not None:
        return member
    try:
        result = guild_request(f"/members/{discord_id}")
    except requests.exceptions.RequestException:
        return
    if not result or result.get("message") == "Unknown Member":
        return None
    cache.set(f"discord_member:{discord_id}", result, timeout=3600)
    return result


@cache.memoize(timeout=3600)
def get_discord_roles():
    if not DISCORD_BOT_TOKEN:
        return {}
    roles = guild_request("/roles")
    return {role["name"]: role["id"] for role in roles}


def send_channel_message(message, channel=DiscordChannels.NOTIFICATION, logger=getLogger(__name__)):
    """Send message to a channel by DiscordChannels enum"""
    if not DISCORD_BOT_TOKEN:
        logger.debug("DISCORD_BOT_TOKEN is not set, skipping Discord message")
        return

    channel_id = channel.value if isinstance(channel, DiscordChannels) else channel
    if not channel_id:
        logger.debug(f"Discord channel {channel} is not configured, skipping message")
        return

    try:
        json_data = dict(content=message)
        discord_request(f"/channels/{channel_id}/messages", method="POST", json=json_data)
        logger.debug(f"Sent Discord message to channel {channel_id}")
    except Exception as e:
        logger.error(f"Failed to send Discord message: {e}")


def send_user_message(message, discord_id, logger=getLogger(__name__)):
    """Send a direct message to a Discord user"""
    if not DISCORD_BOT_TOKEN:
        logger.debug("DISCORD_BOT_TOKEN is not set, skipping Discord DM")
        return

    if not discord_id:
        logger.debug("discord_id is not set, skipping Discord DM")
        return

    try:
        # Create DM channel
        dm_channel = discord_request("/users/@me/channels", method="POST", json={"recipient_id": discord_id})
        if not dm_channel:
            logger.warning(f"Failed to create DM channel for user {discord_id} (rate limited)")
            return
        channel_id = dm_channel["id"]
        # Send message
        discord_request(f"/channels/{channel_id}/messages", method="POST", json={"content": message})
        logger.debug(f"Sent Discord DM to user {discord_id}")
    except Exception as e:
        logger.error(f"Failed to send Discord DM: {e}")


def add_role(discord_id, role_name, logger=getLogger(__name__)):
    roles = get_discord_roles()
    role_id = roles.get(role_name)
    if not role_id:
        logger.debug(f"Role '{role_name}' not found in Discord server, skipping")
        return
    try:
        guild_request(f"/members/{discord_id}/roles/{role_id}", method="PUT")
    except Exception as e:
        logger.error(f"Failed to add role '{role_name}': {e}")
