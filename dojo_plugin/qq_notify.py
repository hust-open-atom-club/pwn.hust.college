"""QQ official bot notifications for solved dojo challenges.

Keep models, settings/admin endpoints and delivery logic in one module.
Requires a runtime-only /var/data/qq_notify.yaml (see qq_notify.example.yaml).
"""

import datetime
import hashlib
import logging
import os
import re
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yaml
from flask import Blueprint, current_app, render_template, request
from sqlalchemy.exc import IntegrityError
from CTFd.models import db
from CTFd.utils.decorators import admins_only, authed_only
from CTFd.utils.user import get_current_user

from .models import DojoChallenges
from .utils.dojo import get_current_dojo_challenge

logger = logging.getLogger(__name__)
qq_notify = Blueprint("qq_notify", __name__)
CONFIG_PATH = Path(os.getenv("QQ_NOTIFY_CONFIG", "/var/data/qq_notify.yaml"))
GROUP_OPENID_RE = re.compile(r"^[A-Za-z0-9_-]{8,255}$")
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

# This is deliberately a best-effort, in-process delivery mechanism. It does
# not access the SQLAlchemy session from the background threads.
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qq-solve")
_token_lock = threading.Lock()
_access_token = None
_access_token_expires = 0.0


class QQGroup(db.Model):
    __tablename__ = "qq_notification_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    group_openid = db.Column(db.String(255), nullable=False, unique=True)
    bind_code_hash = db.Column(db.String(64), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    bindings = db.relationship(
        "QQGroupBinding", back_populates="group", cascade="all, delete-orphan"
    )


class QQGroupBinding(db.Model):
    __tablename__ = "qq_notification_bindings"

    # Composite PK enforces one binding per user and group, even under races.
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    group_id = db.Column(
        db.Integer, db.ForeignKey("qq_notification_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    user = db.relationship("Users")
    group = db.relationship("QQGroup", back_populates="bindings")


def _request_data():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def _group_view(group):
    return {"id": group.id, "name": group.name, "enabled": group.enabled}


def user_qq_groups(user_id):
    """Used by the existing /settings page. Never expose group OpenIDs/codes."""
    return (
        QQGroup.query.join(QQGroupBinding, QQGroup.id == QQGroupBinding.group_id)
        .filter(QQGroupBinding.user_id == user_id)
        .order_by(QQGroup.name)
        .all()
    )


@qq_notify.route("/qq-notify/bind", methods=["POST"])
@authed_only
def bind_group():
    data = _request_data()
    code = data.get("code", "")
    if not isinstance(code, str) or not CODE_RE.fullmatch(code):
        return {"success": False, "error": "无效的绑定码"}, 400

    digest = hashlib.sha256(code.encode("ascii")).hexdigest()
    group = QQGroup.query.filter_by(bind_code_hash=digest, enabled=True).first()
    if group is None:
        return {"success": False, "error": "绑定码不存在或群组已停用"}, 400

    user_id = get_current_user().id
    try:
        db.session.add(QQGroupBinding(user_id=user_id, group_id=group.id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "error": "你已经绑定过这个群组"}, 409
    return {"success": True, "group": _group_view(group)}


@qq_notify.route("/qq-notify/unbind/<int:group_id>", methods=["POST"])
@authed_only
def unbind_group(group_id):
    binding = QQGroupBinding.query.filter_by(
        user_id=get_current_user().id, group_id=group_id
    ).first()
    if binding is None:
        return {"success": False, "error": "没有找到该绑定"}, 404
    db.session.delete(binding)
    db.session.commit()
    return {"success": True}


@qq_notify.route("/admin/qq-notify")
@admins_only
def admin_page():
    groups = QQGroup.query.order_by(QQGroup.id.desc()).all()
    return render_template("admin_qq_notify.html", groups=groups)


def _new_code():
    code = secrets.token_urlsafe(24)
    return code, hashlib.sha256(code.encode("ascii")).hexdigest()


@qq_notify.route("/qq-notify/admin/groups", methods=["POST"])
@admins_only
def create_group():
    data = _request_data()
    name = data.get("name", "")
    openid = data.get("group_openid", "")
    if not isinstance(name, str) or not (1 <= len(name.strip()) <= 128):
        return {"success": False, "error": "群组名称长度必须为 1~128"}, 400
    if not isinstance(openid, str) or not GROUP_OPENID_RE.fullmatch(openid):
        return {"success": False, "error": "Group OpenID 格式不正确"}, 400

    code, digest = _new_code()
    group = QQGroup(name=name.strip(), group_openid=openid, bind_code_hash=digest)
    try:
        db.session.add(group)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "error": "Group OpenID 已存在"}, 409
    # Raw code is returned once. The database only stores its SHA-256 digest.
    return {"success": True, "group": _group_view(group), "bind_code": code}


@qq_notify.route("/qq-notify/admin/groups/<int:group_id>/rotate", methods=["POST"])
@admins_only
def rotate_group_code(group_id):
    group = QQGroup.query.get_or_404(group_id)
    code, group.bind_code_hash = _new_code()
    db.session.commit()
    return {"success": True, "group": _group_view(group), "bind_code": code}


@qq_notify.route("/qq-notify/admin/groups/<int:group_id>/toggle", methods=["POST"])
@admins_only
def toggle_group(group_id):
    group = QQGroup.query.get_or_404(group_id)
    group.enabled = not group.enabled
    db.session.commit()
    return {"success": True, "group": _group_view(group)}


@qq_notify.route("/qq-notify/admin/groups/<int:group_id>/delete", methods=["POST"])
@admins_only
def delete_group(group_id):
    group = QQGroup.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return {"success": True}


def _config():
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return data.get("qq", {}) if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("QQ notifier configuration unavailable: %s", exc)
        return {}


def _get_token(app_id, app_secret):
    global _access_token, _access_token_expires
    with _token_lock:
        if _access_token and time.monotonic() < _access_token_expires:
            return _access_token
        resp = requests.post(
            "https://bots.qq.com/app/getAppAccessToken",
            json={"appId": app_id, "clientSecret": app_secret},
            timeout=(2, 5),
        )
        resp.raise_for_status()
        result = resp.json()
        if not result.get("access_token"):
            raise RuntimeError("QQ token response did not contain access_token")
        _access_token = result["access_token"]
        _access_token_expires = (
            time.monotonic() + max(0, int(result.get("expires_in", 7200)) - 120)
        )
        return _access_token


def _broadcast(group_openids, content, app):
    """Network-only worker: no Flask request context or database queries."""
    config = _config()
    if not config.get("enabled", False):
        return
    if not config.get("app_id") or not config.get("app_secret"):
        app.logger.warning("QQ notification skipped: app_id/app_secret missing")
        return
    try:
        token = _get_token(str(config["app_id"]), str(config["app_secret"]))
    except Exception:
        app.logger.exception("Failed to acquire QQ bot access token")
        return

    for openid in group_openids:
        try:
            resp = requests.post(
                "https://api.sgroup.qq.com/v2/groups/{}/messages".format(openid),
                headers={"Authorization": "QQBot {}".format(token)},
                json={"msg_type": 0, "content": content},
                timeout=(2, 5),
            )
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("code") not in (None, 0):
                raise RuntimeError("QQ API error: {}".format(payload.get("code")))
        except Exception:
            # One failure cannot prevent other subscribed groups from delivery.
            app.logger.exception("Failed to send QQ solve notice to group %s", openid)


def _solve_details(user, challenge):
    """Prefer current container's dojo context; never guess shared imports."""
    selected = None
    try:
        candidate = get_current_dojo_challenge(user)
        if candidate and candidate.challenge_id == challenge.id:
            selected = candidate
    except Exception:
        logger.exception("Failed to determine current dojo challenge")
    if selected is None:
        matches = DojoChallenges.query.filter_by(challenge_id=challenge.id).limit(2).all()
        if len(matches) == 1:
            selected = matches[0]
    if selected is None:
        # No reliable dojo/module for a shared challenge, so never misattribute.
        return None
    return (selected.dojo.name or selected.dojo.id,
            selected.module.name or selected.module.id,
            selected.name or selected.id)


def notify_user_solve(user, challenge):
    """Called after the first successful CTFd solve has committed."""
    if user.hidden:
        return
    groups = (
        QQGroup.query.join(QQGroupBinding, QQGroup.id == QQGroupBinding.group_id)
        .filter(QQGroupBinding.user_id == user.id, QQGroup.enabled.is_(True))
        .all()
    )
    if not groups:
        return
    details = _solve_details(user, challenge)
    if not details:
        logger.warning("QQ notice skipped: ambiguous dojo for challenge_id=%s", challenge.id)
        return
    dojo_name, module_name, challenge_name = details
    content = (
        "🏆 pwn.hust.college 解题播报\n"
        "恭喜 {} 成功完成题目！\n"
        "道馆：{}\n模块：{}\n题目：{}"
    ).format(user.name, dojo_name, module_name, challenge_name)
    openids = tuple({group.group_openid for group in groups})
    app = current_app._get_current_object()
    _executor.submit(_broadcast, openids, content, app)
