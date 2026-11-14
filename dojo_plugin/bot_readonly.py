"""Dedicated, strictly read-only public-data API for enabled QQ groups.

No CTFd user token, no challenge/container mutation, no private dojo access.
Caller must supply an enabled QQ group OpenID.
"""

import re

from flask import Blueprint, abort, request
from .models import Dojos
from .models.config import DOJO_PREREQUISITES
from .qq_notify import QQGroup
from .api.v1.scoreboard import get_scoreboard_for


bot_readonly = Blueprint("pwncollege_bot_readonly", __name__, url_prefix="/pwncollege_api/v1/bot")
DOJO_RE = re.compile(r"[a-z0-9-]{1,32}(?:~[a-f0-9]{8})?\Z")
PART_RE = re.compile(r"[a-z0-9-]{1,32}\Z")
GROUP_RE = re.compile(r"[A-Za-z0-9_-]{8,255}\Z")


@bot_readonly.before_request
def authorize():
    """The bot is NOT authenticated as any CTFd user or administrator."""
    if request.method != "GET":
        abort(405)
    group = request.headers.get("X-PWN-QQ-Group", "")
    if not GROUP_RE.fullmatch(group):
        abort(403)
    if QQGroup.query.filter_by(group_openid=group, enabled=True).first() is None:
        abort(403)


@bot_readonly.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _is_public_dojo(dojo):
    """Avoid exporting course/hidden/password-protected learning materials."""
    return (
        not dojo.password
        and dojo.type not in ("hidden", "course")
        and (dojo.official or dojo.type == "public")
    )


def _dojo(value, *, content=False):
    if not DOJO_RE.fullmatch(value):
        abort(404)
    dojo = Dojos.from_id(value).first()
    # Only universally public dojos; never inherit an admin or student session.
    if not dojo or not _is_public_dojo(dojo):
        abort(404)
    # The web UI gates these challenges behind completion of prerequisite dojos.
    # No QQ identity -> CTFd identity link is available, so fail closed for content.
    if content and dojo.id in DOJO_PREREQUISITES:
        abort(404)
    return dojo


def _module(dojo, value):
    if not PART_RE.fullmatch(value):
        abort(404)
    module = next((item for item in dojo.modules if item.id == value), None)
    if module is None or not any(c.visible() for c in module.challenges):
        abort(404)
    return module


def _challenge(module, value):
    if not PART_RE.fullmatch(value):
        abort(404)
    challenge = next((item for item in module.challenges if item.id == value and item.visible()), None)
    if challenge is None:
        abort(404)
    return challenge


def _dojo_data(dojo):
    return {"id": dojo.reference_id, "name": dojo.name or dojo.id, "prerequisites": bool(dojo.id in DOJO_PREREQUISITES)}


def _module_data(module):
    return {"id": module.id, "name": module.name or module.id}


def _challenge_data(challenge, with_description=False):
    obj = {
        "id": challenge.id,
        "name": challenge.name or challenge.id,
        "level": challenge.level,
    }
    if with_description:
        obj["description"] = (challenge.description or "")[:8000]
    return obj


def _rankings(model):
    try:
        duration = int(request.args.get("duration", "0"))
        page = int(request.args.get("page", "1"))
    except (TypeError, ValueError):
        abort(400)
    if duration not in (0, 7, 30) or not (1 <= page <= 20):
        abort(400)
    rows = get_scoreboard_for(model, duration)
    start = (page - 1) * 10
    # The existing scoreboard query filters hidden users and handles visibility.
    return {
        "duration": duration,
        "page": page,
        "total": len(rows),
        "standings": [
            {
                "rank": int(row["rank"]),
                "name": str(row["name"]),
                "solves": int(row["solves"]),
            }
            for row in rows[start:start + 10]
        ],
    }


@bot_readonly.get("/dojos")
def public_dojos():
    dojos = Dojos.query.filter(
        (Dojos.official.is_(True)) |
        ((Dojos.data["type"] == "public") & (Dojos.password.is_(None)))
    ).order_by(*Dojos.ordering()).limit(200).all()
    return {"dojos": [_dojo_data(dojo) for dojo in dojos if _is_public_dojo(dojo)][:100]}


@bot_readonly.get("/dojos/<dojo_id>/modules")
def public_modules(dojo_id):
    dojo = _dojo(dojo_id, content=True)
    return {"dojo": _dojo_data(dojo), "modules": [_module_data(m) for m in dojo.modules if any(c.visible() for c in m.challenges)][:100]}


@bot_readonly.get("/dojos/<dojo_id>/modules/<module_id>/challenges")
def public_challenges(dojo_id, module_id):
    dojo = _dojo(dojo_id, content=True)
    module = _module(dojo, module_id)
    return {
        "dojo": _dojo_data(dojo),
        "module": _module_data(module),
        "challenges": [_challenge_data(c) for c in module.challenges if c.visible()][:100],
    }


@bot_readonly.get("/dojos/<dojo_id>/modules/<module_id>/challenges/<challenge_id>")
def public_challenge(dojo_id, module_id, challenge_id):
    dojo = _dojo(dojo_id, content=True)
    module = _module(dojo, module_id)
    return {
        "dojo": _dojo_data(dojo),
        "module": _module_data(module),
        "challenge": _challenge_data(_challenge(module, challenge_id), with_description=True),
    }


@bot_readonly.get("/dojos/<dojo_id>/rankings")
def public_dojo_ranking(dojo_id):
    dojo = _dojo(dojo_id)
    return {"dojo": _dojo_data(dojo), **_rankings(dojo)}


@bot_readonly.get("/dojos/<dojo_id>/modules/<module_id>/rankings")
def public_module_ranking(dojo_id, module_id):
    dojo = _dojo(dojo_id)
    module = _module(dojo, module_id)
    return {"dojo": _dojo_data(dojo), "module": _module_data(module), **_rankings(module)}
