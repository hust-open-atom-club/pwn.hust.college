import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

#pylint:disable=redefined-outer-name,use-dict-literal,missing-timeout,unspecified-encoding,consider-using-with,unused-argument

from utils import PROTO, HOST, CONTAINER_NAME, login, dojo_run


def docker_ps_q(filter):
    result = subprocess.run(
        [shutil.which("docker"), "exec", CONTAINER_NAME, "docker", "ps", "-q", "--filter", filter],
        capture_output=True, text=True, check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def get_user_id(user_name):
    db_result = dojo_run("db", input=f"SELECT id FROM users WHERE name = '{user_name}'")
    return int(db_result.stdout.split()[1])


def test_concurrent_start_single_container(example_dojo, random_user):
    user_name, session = random_user
    second_session = login(user_name, user_name)

    barrier = threading.Barrier(2)

    def synchronized_start(start_session):
        barrier.wait(timeout=30)
        return start_session.post(
            f"{PROTO}://{HOST}/pwncollege_api/v1/docker",
            json=dict(dojo=example_dojo, module="world", challenge="earth"),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(synchronized_start, start_session)
            for start_session in (session, second_session)
        ]
        responses = [future.result(timeout=120) for future in futures]

    results = [response.json() for response in responses]
    assert all(response.status_code == 200 for response in responses)
    assert sum(1 for result in results if result["success"]) == 1, \
        f"Expected exactly one of the concurrent starts to succeed: {results}"

    rejected = next(result for result in results if not result["success"])
    assert "already starting" in rejected["error"].lower(), rejected

    user_id = get_user_id(user_name)
    containers = docker_ps_q(f"name=user_{user_id}")
    assert len(containers) == 1, f"Expected a single user_{user_id} container: {containers}"

    active = session.get(f"{PROTO}://{HOST}/pwncollege_api/v1/docker").json()
    assert active["success"], active
    assert active["dojo"] == example_dojo
    assert active["module"] == "world"
    assert active["challenge"] == "earth"
