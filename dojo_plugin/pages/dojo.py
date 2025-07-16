import datetime
import docker
import pytz

from flask import Blueprint, render_template, redirect, abort
from CTFd.models import db, Solves, Challenges, Users, Awards
from CTFd.utils.user import get_current_user,is_admin
from CTFd.utils.decorators.visibility import check_challenge_visibility
from CTFd.utils.helpers import get_infos
from CTFd.cache import cache

from ..utils import render_markdown, module_visible, module_challenges_visible, is_dojo_admin
from ..utils.dojo import dojo_route, get_current_dojo_challenge
from ..models import Dojos, DojoUsers, DojoStudents

dojo = Blueprint("pwncollege_dojo", __name__)


@cache.memoize(timeout=60)
def get_stats(dojo):
    docker_client = docker.from_env()
    filters = {
        "name": "user_",
        "label": f"dojo.dojo_id={dojo.reference_id}"
    }
    containers = docker_client.containers.list(filters=filters, ignore_removed=True)

    now = datetime.datetime.now()
    active = 0.0
    for container in containers:
        created = container.attrs["Created"].split(".")[0]
        uptime = now - datetime.datetime.fromisoformat(created)
        hours = max(uptime.seconds // (60 * 60), 1)
        active += 1 / hours

    # TODO: users and solves query is slow, so we'll just leave it out for now
    # TODO: we need to index tables for this to be fast
    return {
        "active": int(active),
        "users": "-", # int(dojo.solves().group_by(Solves.user_id).count()),
        "challenges": int(len(dojo.challenges)),
        "solves": "-", # int(dojo.solves().count()),
    }


@dojo.route("/<dojo>")
@dojo.route("/<dojo>/")
@dojo_route
@check_challenge_visibility
def listing(dojo):
    infos = get_infos()
    user = get_current_user()
    dojo_user = DojoUsers.query.filter_by(dojo=dojo, user=user).first()
    stats = get_stats(dojo)
    # merge from 58e795eeadbd4ce81d16422aa83daca3a129fa91
    if dojo.award and "emoji" in dojo.award:
        awards = Awards.query.where(Awards.category==dojo.hex_dojo_id, Awards.name==dojo.award["emoji"]).order_by(Awards.date.desc()).all()
    elif dojo.award and "belt" in dojo.award:
        awards = Awards.query.where(Awards.type=="belt", Awards.name==dojo.award["belt"]).order_by(Awards.date.desc()).all()
    else:
        awards = [ ]
        
    prerequisite_dojo_sub= []
    if not dojo.is_admin():
        check_result, prerequisite_dojo = dojo.check_prerequisites(user)
        
        # 确保 prerequisite_dojo 不是 None
        if prerequisite_dojo is None:
            prerequisite_dojo = []

        for prerequisite in prerequisite_dojo:
            prerequisite_dojo_sub.append(Dojos.query.filter(Dojos.id == prerequisite).first())
        if not check_result:
            #infos.append("请完成前置关卡 '{}' 后再进入此关卡".format(prerequisite_dojo.dojo_id))
            return render_template("dojo_error.html", prerequisite_dojo_sub=prerequisite_dojo_sub, user=user, dojo_user=dojo_user, stats=stats, infos=infos,dojo_locked=dojo)  
        
    return render_template(
        "dojo.html",
        dojo=dojo,
        user=user,
        dojo_user=dojo_user,
        stats=stats,
        infos=infos,
        awards=awards,
    )


@dojo.route("/<dojo>/<module>")
@dojo_route
@check_challenge_visibility
def view_module(dojo, module):
    user = get_current_user()
    user_solves = set(solve.challenge_id for solve in (
        module.solves(user=user, ignore_visibility=True, ignore_admins=False) if user else []
    ))
    total_solves = dict(module.solves()
                        .group_by(Solves.challenge_id)
                        .with_entities(Solves.challenge_id, db.func.count()))
    current_dojo_challenge = get_current_dojo_challenge()

    student = DojoStudents.query.filter_by(dojo=dojo, user=user).first()
    assessments = []
    if student or dojo.is_admin(user):
        now = datetime.datetime.now(datetime.timezone.utc)
        for assessment in module.assessments:
            date = datetime.datetime.fromisoformat(assessment["date"])
            until = date.astimezone(datetime.timezone.utc) - now
            if until < datetime.timedelta(0):
                continue
            date = str(date)
            until = " ".join(
                f"{count} {unit}{'s' if count != 1 else ''}" for count, unit in zip(
                    (until.days, *divmod(until.seconds // 60, 60)),
                    ("day", "hour", "minute")
                ) if count
            ) or "now"
            assessments.append(dict(
                name=assessment["type"].title(),
                date=date,
                until=until,
            ))

    return render_template(
        "module.html",
        dojo=dojo,
        module=module,
        challenges=module.visible_challenges(),
        user_solves=user_solves,
        total_solves=total_solves,
        user=user,
        current_dojo_challenge=current_dojo_challenge,
        assessments=assessments,
    )
