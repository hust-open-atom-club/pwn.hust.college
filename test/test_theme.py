import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_TEMPLATE = REPOSITORY_ROOT / "dojo_theme/templates/settings.html"

PANEL_PATTERN = re.compile(r'tab-pane[^>]*\bid="([a-z0-9-]+)"')
NAV_LINK_PATTERN = re.compile(r'nav-link[^>]*\bhref="#([a-z0-9-]+)"')
# 前置空白是必需的：否则 data-token-id="{{ token.id }}" 中的 "id=" 会被误当成 id 属性
ID_ATTRIBUTE_PATTERN = re.compile(r'(?:^|\s)id="([^"]+)"')
FOR_ATTRIBUTE_PATTERN = re.compile(r'(?:^|\s)for="([^"]+)"')


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


def test_settings_ids_are_unique_and_labels_resolve():
    template = SETTINGS_TEMPLATE.read_text(encoding="utf-8")

    idValues = ID_ATTRIBUTE_PATTERN.findall(template)
    duplicateIds = sorted({value for value in idValues if idValues.count(value) > 1})
    assert not duplicateIds, f"{SETTINGS_TEMPLATE} 中存在重复 id: {duplicateIds}"

    knownIds = set(idValues)
    danglingFors = sorted(
        target for target in FOR_ATTRIBUTE_PATTERN.findall(template) if target not in knownIds
    )
    assert not danglingFors, (
        f"{SETTINGS_TEMPLATE} 中这些 label 的 for 指向不存在的 id: {danglingFors}"
    )
