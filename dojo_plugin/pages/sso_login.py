from flask import Blueprint, url_for, request, redirect
from CTFd.utils.security.auth import login_user

from ..api.v1.sso_login import CASBackend

sso = Blueprint("pwncollege_sso", __name__)


@sso.route('/cas-login/')
def cas_login():
    ticket = request.args.get('ticket')
    casbackend = CASBackend()
    if ticket:
        user = casbackend.authenticate(ticket)
        if user:
            login_user(user)
            return redirect(url_for('pwncollege_dojos.listing'))
        else:
            return redirect(url_for("auth.login"))
    else:
        return redirect(CASBackend.get_login_url())
