import random
import string
import pytest

#pylint:disable=redefined-outer-name,use-dict-literal,missing-timeout,unspecified-encoding,consider-using-with

from utils import TEST_DOJOS_LOCATION
from utils import login, make_dojo_official, create_dojo, create_dojo_yml

def pytest_configure(config):
    config.addinivalue_line("markers", "dependency: mark test as dependent on other tests")

@pytest.fixture(scope="session")
def admin_session():
    session = login("admin", "admin")
    yield session


@pytest.fixture
def random_user():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session


@pytest.fixture(scope="session")
def completionist_user():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session


@pytest.fixture(scope="session")
def guest_dojo_admin():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session

@pytest.fixture(scope="session")
def example_dojo(admin_session):
    rid = create_dojo("github","hust-open-atom-club/example-dojo", session=admin_session)
    make_dojo_official(rid, admin_session)
    return rid

@pytest.fixture(scope="session")
def simple_award_dojo(admin_session):
    return create_dojo_yml(open(TEST_DOJOS_LOCATION / "simple_award_dojo.yml").read(), session=admin_session)
