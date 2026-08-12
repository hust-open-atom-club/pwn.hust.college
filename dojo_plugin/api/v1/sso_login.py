from urllib.parse import urlencode, urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError

from CTFd.models import  Users, db
from CTFd.utils import user as current_user
from CTFd.utils.helpers import error_for, get_errors, markup
from CTFd.utils.logging import log


from xml.etree import ElementTree

class Settings:
    def __init__(self):
        self.DEBUG = True
        self.CAS_SERVER_URL = 'https://pass.hust.edu.cn/cas/login'
        self.CAS_ADMIN_PREFIX = None
        self.CAS_EXTRA_LOGIN_PARAMS = None
        self.CAS_IGNORE_REFERER = False
        self.CAS_LOGOUT_COMPLETELY = True
        self.CAS_REDIRECT_URL = 'https://pwn.cse.hust.edu.cn/cas-login/'
        self.CAS_RETRY_LOGIN = False
        self.CAS_VERSION = '2'

    def __getattr__(self, item):
        raise AttributeError(f'Setting {item} not found')

settings = Settings()



def _verify_cas2(ticket, service):
    """Verifies CAS 2.0+ XML-based authentication ticket."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    params = {'ticket': ticket, 'service': service}
    url = urljoin(settings.CAS_SERVER_URL, 'proxyValidate') + '?' + urlencode(params)
    request = Request(url, headers=headers)

    try:
        with urlopen(request,timeout=2) as page:
            response = page.read()
            tree = ElementTree.fromstring(response)
            if tree[0].tag.endswith('authenticationSuccess'):
                return tree[0][0].text
            else:
                return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None


def register_sso(studentID):
    errors = get_errors()
    name = studentID.strip()
    email_address = studentID.strip().lower()+"@hust.edu.cn"
    password = ""
    bracket_id = None
    oauth_id = int(studentID[1:])
    # website = request.form.get("website")
    # affiliation = request.form.get("affiliation")
    # country = request.form.get("country")
    # registration_code = str(request.form.get("registration_code", ""))
    # bracket_id = request.form.get("bracket_id", None)

    names = (
        Users.query.add_columns(Users.name, Users.id).filter_by(name=name).first()
    )
    emails = (
        Users.query.add_columns(Users.email, Users.id)
        .filter_by(email=email_address)
        .first()
    )
    if names:
        errors.append("That user name is already taken")
    if emails:
        errors.append("That email has already been used")

    user = Users(
        name=name,
        email=email_address,
        password=password,
        oauth_id=oauth_id,
        verified=True,
    )
    db.session.add(user)
    db.session.commit()

    log(
        "registrations",
        format="[{date}] {ip} - {name} registered with {email}",
        name=user.name,
        email=user.email,
    )
    db.session.close()
    return user



class CASBackend(object):
    """CAS authentication backend"""

    def authenticate(self,ticket):
        service = settings.CAS_REDIRECT_URL
        username = _verify_cas2(ticket, service)
        if username is None:
            return None
        user = Users.query.filter_by(oauth_id=username[1:]).first()

        if user :
            return user
        else:
            # user will have an "unusable" password
            user = register_sso(username)
            return user

    def get_user(self, user_id):
        """Retrieve the user's entry in the User model if it exists"""

    def get_login_url():
        """Generates CAS login URL"""
        params = {'service': settings.CAS_REDIRECT_URL}
        #return urlopen(settings.CAS_SERVER_URL)
        return urljoin(settings.CAS_SERVER_URL, 'login') + '?' + urlencode(params)
