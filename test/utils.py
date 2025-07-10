import subprocess
import requests
import pathlib
import shutil
import re
import os
import http.client as http_client
import tempfile 

PROTO="http"
HOST="localhost"
CONTAINER_NAME = os.environ.get("CONTAINER_NAME", "dojo-test")
TEST_DOJOS_LOCATION = pathlib.Path(__file__).parent / "dojos"


def parse_csrf_token(text):
    match = re.search("'csrfNonce': \"(\\w+)\"", text)
    assert match, "Failed to find CSRF token"
    return match.group(1)


def login(name, password, *, success=True, register=False, email=None):
    session = requests.Session()
    endpoint = "login" if not register else "register"
    
    login_url = f"{PROTO}://{HOST}/{endpoint}"
    login_page = session.get(login_url)
    
    nonce = parse_csrf_token(login_page.text)
    
    data = { "name": name, "password": password, "nonce": nonce }
    if register:
        data["email"] = email or f"{name}@example.com"
    
    response = session.post(login_url, data=data, allow_redirects=False)
    
    if not success:
        assert response.status_code == 200, f"Expected {endpoint} failure (status code 200), but got {response.status_code}"
        return session
    assert response.status_code == 302, f"Expected {endpoint} success (status code 302), but got {response.status_code}"
    
    home_page = session.get(f"{PROTO}://{HOST}/")
    session.headers["CSRF-Token"] = parse_csrf_token(home_page.text)
    
    return session

def make_dojo_official(dojo_rid, admin_session):
    response = admin_session.post(f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/{dojo_rid}/promote-dojo", json={})
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code} - {response.json()}"

def generate_ssh_keypair():
    temp_dir = tempfile.TemporaryDirectory()
    key_dir = pathlib.Path(temp_dir.name)

    public_key = key_dir / "key.pub"
    private_key = key_dir / "key"

    subprocess.run(["ssh-keygen",
                    "-t", "ed25519",
                    "-P", "",
                    "-C", "",
                    "-f", str(private_key)],
                    check=True,
                    capture_output=True)

    return (public_key.read_text().strip(), private_key.read_text())

def create_dojo(repository_type, repository, *, session):
    public_key, private_key = generate_ssh_keypair()
    create_dojo_json = {"repository_type": repository_type, "repository": repository, 
                        "public_key": public_key, "private_key": private_key}
    response = session.post(f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/create", json=create_dojo_json)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code} - {response.json()}"
    dojo_reference_id = response.json()["dojo"]
    return dojo_reference_id

def create_dojo_yml(spec, *, session):
    response = session.post(f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/create-spec", json={"spec": spec})
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code} - {response.json()}"
    dojo_reference_id = response.json()["dojo"]
    return dojo_reference_id

def dojo_run(*args, **kwargs):
    kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return subprocess.run(
        [shutil.which("docker"), "exec", "-i", CONTAINER_NAME, "dojo", *args],
        check=kwargs.pop("check", True), **kwargs
    )


def workspace_run(cmd, *, user, root=False, **kwargs):
    args = [ "enter" ]
    if root:
        args += [ "-s" ]
    args += [ user ]
    return dojo_run(*args, input=cmd, check=True, **kwargs)
    
