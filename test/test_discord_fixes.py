"""
Unit tests for Discord review fixes.
Loads modules directly via importlib to avoid the heavy dojo_plugin dependency chain.
"""
import sys
import types
import importlib
import importlib.util
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# ---------------------------------------------------------------------------
# Helpers: load individual .py files without triggering package __init__.py
# ---------------------------------------------------------------------------

def _stub(name):
    """Register a stub module so imports of `name` don't fail."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = []
        sys.modules[name] = mod
    return sys.modules[name]

# Stub the top-level packages/subpackages that would trigger heavy imports
for _pkg in [
    "dojo_plugin", "dojo_plugin.config", "dojo_plugin.models",
    "dojo_plugin.utils", "dojo_plugin.utils.dojo",
    "dojo_plugin.api", "dojo_plugin.api.v1",
    "flask", "flask_restx",
    "CTFd", "CTFd.models", "CTFd.cache",
    "CTFd.utils", "CTFd.utils.decorators", "CTFd.utils.user",
]:
    _stub(_pkg)

# Provide attributes the target modules access at import time
sys.modules["flask"].url_for = MagicMock(return_value="/mock")
sys.modules["flask"].request = MagicMock()
sys.modules["flask"].Request = MagicMock()

sys.modules["flask_restx"].Namespace = MagicMock()
sys.modules["flask_restx"].Resource = type("Resource", (), {})

sys.modules["CTFd.cache"].cache = MagicMock()
sys.modules["CTFd.cache"].cache.memoize = lambda **kw: (lambda f: f)

sys.modules["CTFd.models"].db = MagicMock()
sys.modules["CTFd.utils.decorators"].authed_only = lambda f: f
sys.modules["CTFd.utils.user"].get_current_user = MagicMock()

# Config values
sys.modules["dojo_plugin.config"].DISCORD_CLIENT_ID = "fake-id"
sys.modules["dojo_plugin.config"].DISCORD_CLIENT_SECRET = "fake-secret"
sys.modules["dojo_plugin.config"].DISCORD_BOT_TOKEN = "fake-bot-token"
sys.modules["dojo_plugin.config"].DISCORD_GUILD_ID = "fake-guild"

# Models
sys.modules["dojo_plugin.models"].DiscordUsers = MagicMock()
sys.modules["dojo_plugin.models"].DiscordUserActivity = MagicMock()

# Utils
sys.modules["dojo_plugin.utils.dojo"].get_current_dojo_challenge = MagicMock()
sys.modules["dojo_plugin.utils.dojo"].dojo_route = lambda f: f


def _load_module_from_file(mod_name, file_path):
    """Load a single .py file as a module, skipping __init__.py chains."""
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load the two modules under test
discord_utils = _load_module_from_file(
    "dojo_plugin.utils.discord",
    "dojo_plugin/utils/discord.py",
)
discord_api = _load_module_from_file(
    "dojo_plugin.api.v1.discord",
    "dojo_plugin/api/v1/discord.py",
)


# ===========================================================================
# Fix 1: discord_request — 429 returns None instead of blocking with sleep
# ===========================================================================

class TestDiscordRequestRateLimit:
    """Critical fix 1: discord_request should not block on 429."""

    @patch.object(discord_utils.requests, "request")
    def test_429_returns_none_without_sleeping(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"retry_after": 5}
        mock_request.return_value = mock_response

        result = discord_utils.discord_request("/test")

        assert result is None
        assert mock_request.call_count == 1  # no retry loop

    @patch.object(discord_utils.requests, "request")
    def test_200_json_returns_data(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response

        result = discord_utils.discord_request("/test")
        assert result == {"id": "123"}


# ===========================================================================
# Fix 1 (cont): send_user_message handles None from rate-limited DM channel
# ===========================================================================

class TestSendUserMessageRateLimit:
    @patch.object(discord_utils, "discord_request", return_value=None)
    @patch.object(discord_utils, "DISCORD_BOT_TOKEN", "fake-token")
    def test_rate_limited_dm_channel_does_not_crash(self, mock_req):
        discord_utils.send_user_message("hello", "user123")
        mock_req.assert_called_once()


# ===========================================================================
# Fix 2: end_stamp copy-paste bug
# ===========================================================================

def _mock_request(args_dict=None, json_data=None, json_error=False, auth_token=None):
    """Build a mock request object with .args, .get_json(), .headers."""
    req = MagicMock()
    req.args = MagicMock()
    req.args.get = lambda key, default=None: (args_dict or {}).get(key, default)
    if json_error:
        req.get_json = MagicMock(return_value=None)  # simulates invalid JSON
    else:
        req.get_json = MagicMock(return_value=json_data)  # accepts any kwargs like silent=True
    req.headers = MagicMock()
    req.headers.get = lambda key, default=None: (
        f"Bearer {auth_token}" if key == "Authorization" and auth_token else default
    )
    return req


class TestGetUserActivityDateParsing:
    """Critical fix 2: end should use end_stamp, not start_stamp."""

    @patch.object(discord_api, "get_user_activity_prop")
    def test_start_and_end_parsed_independently(self, mock_prop):
        mock_prop.return_value = {"success": True, "thanks": 0}
        req = _mock_request(args_dict={"start": "2025-01-01", "end": "2025-06-01"})

        discord_api.get_user_activity("user1", "thanks", req)

        args = mock_prop.call_args[0]
        assert args[2] == datetime(2025, 1, 1)  # start
        assert args[3] == datetime(2025, 6, 1)  # end — was broken (equaled start)
        assert args[2] != args[3]

    def test_invalid_start_returns_400(self):
        req = _mock_request(args_dict={"start": "bad"})
        result = discord_api.get_user_activity("u1", "thanks", req)
        assert result == ({"success": False, "error": "invalid start format"}, 400)

    def test_invalid_end_returns_400(self):
        req = _mock_request(args_dict={"end": "bad"})
        result = discord_api.get_user_activity("u1", "thanks", req)
        assert result == ({"success": False, "error": "invalid end format"}, 400)


# ===========================================================================
# Fix 3: get_json(silent=True) — handles invalid/missing JSON
# ===========================================================================

class TestPostUserActivityJsonParsing:
    """Warning fix 1: None from get_json should not crash with TypeError."""

    def test_invalid_json_returns_400_not_500(self):
        req = _mock_request(json_error=True, auth_token="fake-secret")
        res, code = discord_api.post_user_activity("u1", "memes", req)
        assert code == 400
        assert "not found" in res["error"]

    def test_missing_field_returns_400(self):
        req = _mock_request(json_data={"source_user_id": "u1"}, auth_token="fake-secret")
        res, code = discord_api.post_user_activity("u1", "memes", req)
        assert code == 400


# ===========================================================================
# Fix 4: Invalid message_timestamp returns 400
# ===========================================================================

class TestPostUserActivityTimestamp:
    """Warning fix 2: invalid message_timestamp should return 400."""

    def test_invalid_timestamp_returns_400(self):
        data = {
            "source_user_id": "u1",
            "guild_id": "g1",
            "channel_id": "c1",
            "message_id": "m1",
            "message_timestamp": "not-a-timestamp",
        }
        req = _mock_request(json_data=data, auth_token="fake-secret")
        res, code = discord_api.post_user_activity("u1", "memes", req)
        assert code == 400
        assert "timestamp" in res["error"].lower()


# ===========================================================================
# Fix 5: auth_check — malformed Authorization header
# ===========================================================================

class TestAuthCheck:
    """Warning fix 3: auth_check should handle malformed headers."""

    def test_no_header(self):
        res, code = discord_api.auth_check(None)
        assert code == 401

    def test_empty_string(self):
        res, code = discord_api.auth_check("")
        assert code == 401

    def test_bearer_without_token(self):
        res, code = discord_api.auth_check("Bearer ")
        assert code == 401

    def test_just_bearer_no_space(self):
        res, code = discord_api.auth_check("Bearer")
        assert code == 401

    def test_wrong_scheme(self):
        res, code = discord_api.auth_check("Basic abc123")
        assert code == 401

    @patch.object(discord_api, "DISCORD_CLIENT_SECRET", "correct-secret")
    def test_wrong_token(self):
        res, code = discord_api.auth_check("Bearer wrong-secret")
        assert code == 401

    @patch.object(discord_api, "DISCORD_CLIENT_SECRET", "correct-secret")
    def test_correct_token(self):
        res, code = discord_api.auth_check("Bearer correct-secret")
        assert res is None
        assert code is None
