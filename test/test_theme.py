import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_TEMPLATE = REPOSITORY_ROOT / "dojo_theme/templates/settings.html"

PANEL_PATTERN = re.compile(r'tab-pane[^>]*\bid="([a-z0-9-]+)"')
NAV_LINK_PATTERN = re.compile(r'nav-link[^>]*\bhref="#([a-z0-9-]+)"')


def test_settings_panels_are_reachable_from_navigation():
    template = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    panels = set(PANEL_PATTERN.findall(template))
    navLinks = set(NAV_LINK_PATTERN.findall(template))

    assert panels, f"{SETTINGS_TEMPLATE} 中未找到任何 tab-pane"

    unreachable = panels - navLinks
    assert not unreachable, (
        f"{SETTINGS_TEMPLATE} 中这些面板没有导航入口，用户无法访问: {sorted(unreachable)}"
    )

    dangling = navLinks - panels
    assert not dangling, (
        f"{SETTINGS_TEMPLATE} 中这些导航链接指向不存在的面板: {sorted(dangling)}"
    )
