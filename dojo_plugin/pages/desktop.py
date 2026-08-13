from flask import Blueprint, render_template
from CTFd.utils.decorators import admins_only

from ..utils import get_active_users


desktop = Blueprint("pwncollege_desktop", __name__)


@desktop.route("/admin/desktops", methods=["GET"])
@admins_only
def view_all_desktops():
    # active_desktops=True here would filter out only desktops that have been connected to, but that is too slow in
    # the current implementation...
    return render_template("admin_desktops.html", users=get_active_users())
