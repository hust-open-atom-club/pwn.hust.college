from pathlib import Path

import requests
import pytest

#pylint:disable=redefined-outer-name,use-dict-literal,missing-timeout,unspecified-encoding,consider-using-with,unused-argument

from utils import PROTO, HOST, create_dojo_yml
from test_running import start_and_solve
import random

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
JS_DIRECTORY = REPOSITORY_ROOT / "dojo_theme" / "static" / "js" / "dojo"

EVIL_REPOSITORY = 'a/b"><img src=x onerror=alert(1)>'

# ---------------------------------------------------------------------------
# 静态契约：来自 API 响应的动态内容不得进入 HTML 渲染路径
# ---------------------------------------------------------------------------

def test_dynamic_errors_render_as_text():
    for name in ["settings.js", "course.js"]:
        source = (JS_DIRECTORY / name).read_text(encoding="utf-8")
        assert ".html(result.error)" not in source, f"{name} 仍以 HTML 渲染动态错误"
        assert ".html(result.warning)" not in source, f"{name} 仍以 HTML 渲染动态警告"


def test_challenge_error_uses_fixed_dom():
    source = (JS_DIRECTORY / "challenges.js").read_text(encoding="utf-8")
    assert '"<code>" + result.error + "</code>"' not in source, "动态错误仍在拼进 HTML 字符串"
    assert 'result_message.find("code").text(result.error)' in source


def test_scoreboard_badges_built_with_attributes():
    source = (JS_DIRECTORY / "scoreboard.js").read_text(encoding="utf-8")
    assert 'title="${badge.text}"' not in source, "badge.text 仍插值进 title 属性"
    assert 'src="/themes/dojo_theme/static/img/dojo/${badge.emoji}' not in source, "badge.emoji 仍插值进 src 属性"
    assert '.attr("title", badge.text)' in source
    assert '.attr("src", `/themes/dojo_theme/static/img/dojo/${badge.emoji}.svg`)' in source


def test_clone_error_link_built_safely():
    source = (JS_DIRECTORY / "settings.js").read_text(encoding="utf-8")
    assert "result.deploy_url" in source, "结构化 deploy_url 未被前端消费"
    assert 'href: result.deploy_url' in source, "链接 href 未通过属性赋值构建"


# ---------------------------------------------------------------------------
# API 行为契约：错误字段按纯文本输出（不做提前转义，由前端 .text() 渲染）
# ---------------------------------------------------------------------------

def test_evil_repository_rejected_without_reflection(admin_session):
    response = admin_session.post(
        f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/create",
        json={"repository_type": "github", "repository": EVIL_REPOSITORY,
              "public_key": "", "private_key": ""},
    )
    assert response.status_code == 400, response.json()
    result = response.json()
    assert not result["success"]
    assert "Invalid repository" in result["error"]
    assert "<img" not in result["error"], "恶意 repository 内容被回显进错误消息"


def test_schema_error_is_raw_text(admin_session):
    # 契约：error 字段是纯数据、不做 HTML 转义（&lt; 之类实体属于双重转义），
    # 渲染安全由前端 .text() 保证（见上方静态契约测试）
    response = admin_session.post(
        f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/create-spec",
        json={"spec": "id: [\"<script>alert(1)</script>\"]\nname: x"},
    )
    assert response.status_code == 400, response.json()
    result = response.json()
    assert not result["success"]
    assert "&lt;" not in result["error"] and "&gt;" not in result["error"], "错误消息被提前转义"
    assert "<script>" in result["error"], "SchemaError 应携带原始内容以便定位问题"


def test_ssh_key_error_is_plain_text(random_user):
    _, session = random_user
    response = session.post(
        f"{PROTO}://{HOST}/pwncollege_api/v1/ssh_key",
        json={"ssh_key": "not-a-valid-key"},
    )
    assert response.status_code == 400, response.json()
    error = response.json()["error"]
    assert "Invalid SSH Key" in error
    assert "<br>" not in error and "<code>" not in error, "错误消息不应包含 HTML 标签"


def _github_reachable():
    try:
        requests.head("https://github.com", timeout=5)
        return True
    except requests.RequestException:
        return False


@pytest.mark.skipif(not _github_reachable(), reason="github.com unreachable from this environment")
@pytest.mark.dependency()
def test_clone_failure_returns_structured_url(admin_session):
    repository = "hust-open-atom-club/nonexistent-repo-for-clone-failure-test"
    response = admin_session.post(
        f"{PROTO}://{HOST}/pwncollege_api/v1/dojo/create",
        json={"repository_type": "github", "repository": repository,
              "public_key": "", "private_key": ""},
    )
    assert response.status_code == 400, response.json()
    result = response.json()
    assert not result["success"]
    assert "Failed to clone" in result["error"]
    assert "<a" not in result["error"], "错误消息不应内嵌 HTML 链接"
    assert result.get("deploy_url") == f"https://github.com/{repository}/settings/keys"


# ---------------------------------------------------------------------------
# 浏览器级回归：恶意 award.emoji 的渲染路径（存储型 XSS）
# ---------------------------------------------------------------------------

EVIL_EMOJI = '"><svg/onload=window.__xss=1>'


def test_malicious_award_emoji_does_not_execute(admin_session, example_dojo, random_user):
    pytest.importorskip("selenium")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    user_name, session = random_user

    spec = (
        f"id: xss-award-{random.randint(1000, 9999)}\n"
        "type: public\n"
        "award:\n"
        f"  emoji: '{EVIL_EMOJI}'\n"
        "  award_at: 1\n"
        "modules:\n"
        "  - import:\n"
        "      dojo: example\n"
        "      module: world\n"
    )
    dojo_rid = create_dojo_yml(spec, session=admin_session)

    # 解一题即可获得 award_at=1 的徽章（恶意 emoji 由此进入该用户的 scoreboard 数据）
    start_and_solve(user_name, session, dojo_rid, "world", "earth")

    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    try:
        driver.get(f"{PROTO}://{HOST}/login")
        driver.add_cookie({"name": "session", "value": session.cookies.get("session")})
        driver.get(f"{PROTO}://{HOST}/dojo/{dojo_rid}/world/")

        WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".scoreboard-emoji")
        )

        executed = driver.execute_script("return Boolean(window.__xss)")
        assert not executed, "恶意 award.emoji 中的脚本在 scoreboard 页面被执行"

        badge_src = driver.execute_script(
            "const el = document.querySelector('.scoreboard-emoji');"
            "return el ? el.getAttribute('src') : null;"
        )
        assert badge_src is not None, "徽章图片元素未渲染"
        assert EVIL_EMOJI in badge_src, f"payload 应以纯数据存在于 src 属性中: {badge_src!r}"
    finally:
        driver.quit()
