"""QQ Official read-only commands for public pwn.hust.college data.

Strictly fixed HTTPS origin and six preapproved GET routes. Does not register
an LLM tool or follow description links. Network egress should additionally
be constrained by deployment firewall policy if process-level isolation matters.
"""

import asyncio
import html
import json
import re
import time
from collections import defaultdict, deque
from urllib.parse import quote

import aiohttp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

# Deliberately NOT configurable and never derived from a message.
ORIGIN = "https://pwn.cse.hust.edu.cn"
PREFIX = "/pwncollege_api/v1/bot"
DOJO_RE = re.compile(r"[a-z0-9-]{1,32}(?:~[a-f0-9]{8})?\Z")
PART_RE = re.compile(r"[a-z0-9-]{1,32}\Z")
GROUP_RE = re.compile(r"[A-Za-z0-9_-]{8,255}\Z")
LIMIT_BYTES = 65536
# Restrict every outbound request to the six read-only route families.
ALLOWED_PATH_RE = re.compile(
    r"/dojos(?:"
    r"|/[a-z0-9-]{1,32}(?:~[a-f0-9]{8})?/(?:"
    r"modules"
    r"|rankings"
    r"|modules/[a-z0-9-]{1,32}/(?:challenges(?:/[a-z0-9-]{1,32})?|rankings)"
    r")"
    r")\Z"
)


class PwnCollegeError(Exception):
    pass


def _id(value, dojo=False):
    check = DOJO_RE if dojo else PART_RE
    if not isinstance(value, str) or not check.fullmatch(value):
        raise PwnCollegeError("参数格式不正确，只允许道馆、模块或题目的 ID。")
    return quote(value, safe="")


def _plain(text, limit=1200):
    """Render user-authored Markdown as inert plain text, not loaded resources."""
    text = str(text or "")
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1（图片省略）", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]{0,4096}>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit] + ("\n……内容已截断，请前往平台官网查看。" if len(text) > limit else "")


def _display_id(value, dojo=False):
    pattern = DOJO_RE if dojo else PART_RE
    return value if isinstance(value, str) and pattern.fullmatch(value) else "ID异常"


class PwnCollegePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._recent = defaultdict(deque)

    def _group(self, event: AstrMessageEvent):
        # QQ Official group events should expose group_openid as group_id.
        # No QQ user identity or ordinary numeric QQ group ID is substituted.
        group = str(event.get_group_id() or "")
        if not GROUP_RE.fullmatch(group):
            raise PwnCollegeError("无法识别 QQ 官方群 OpenID，已拒绝查询。")
        if len(str(self.config.get("read_token", ""))) < 32:
            raise PwnCollegeError("管理员尚未配置只读查询密钥。")
        now = time.monotonic()
        queue = self._recent[group]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= 10:
            raise PwnCollegeError("查询过于频繁，请稍后再试（每群每分钟最多 10 次）。")
        queue.append(now)
        return group

    async def _get(self, group: str, path: str, params=None):
        # Callers use only fixed paths built below; no arbitrary URL input.
        if not ALLOWED_PATH_RE.fullmatch(path):
            raise PwnCollegeError("请求路径不允许。")
        url = ORIGIN + PREFIX + path
        timeout = aiohttp.ClientTimeout(total=7, connect=3)
        headers = {
            "X-PWN-Bot-Token": str(self.config["read_token"]),
            "X-PWN-QQ-Group": group,
            "Accept": "application/json",
        }
        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                trust_env=False,
                cookie_jar=aiohttp.DummyCookieJar(),
            ) as client:
                async with client.get(url, headers=headers, params=params, allow_redirects=False) as response:
                    if 300 <= response.status < 400:
                        raise PwnCollegeError("平台返回了重定向，已拒绝跟随。")
                    if response.status == 403:
                        raise PwnCollegeError("当前群没有查询权限，或只读密钥不正确。")
                    if response.status == 404:
                        raise PwnCollegeError("未找到公开的道馆、模块或题目。")
                    if response.status != 200:
                        raise PwnCollegeError("平台查询暂不可用。")
                    if "application/json" not in response.headers.get("Content-Type", ""):
                        raise PwnCollegeError("平台响应格式不正确。")
                    data = await response.content.read(LIMIT_BYTES + 1)
                    if len(data) > LIMIT_BYTES:
                        raise PwnCollegeError("响应体超过上限，已拒绝处理。")
                    obj = json.loads(data)
                    if not isinstance(obj, dict):
                        raise PwnCollegeError("平台响应格式不正确。")
                    return obj
        except PwnCollegeError:
            raise
        except (aiohttp.ClientError, TimeoutError, asyncio.TimeoutError, ValueError, UnicodeDecodeError):
            logger.warning("PWN read-only API request failed")
            raise PwnCollegeError("查询失败，请稍后再试。") from None

    async def _run(self, event, path, params=None):
        try:
            group = self._group(event)
            return await self._get(group, path, params)
        except PwnCollegeError as exc:
            return {"_error": str(exc)}

    @filter.command_group("pwn")
    def pwn(self):
        pass

    @pwn.command("道馆")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def dojos(self, event: AstrMessageEvent):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        result = await self._run(event, "/dojos")
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        rows = result.get("dojos", [])[:20]
        lines = ["公开道馆（最多展示 20 个）："]
        lines += [
            f"{i}. {_plain(item.get('name'), 55)}  [{_display_id(item.get('id'), dojo=True)}]"
            for i, item in enumerate(rows, 1)
        ]
        yield event.plain_result("\n".join(lines) if rows else "暂无公开道馆。")

    @pwn.command("模块")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def modules(self, event: AstrMessageEvent, dojo: str):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        try:
            path = f"/dojos/{_id(dojo, dojo=True)}/modules"
        except PwnCollegeError as exc:
            yield event.plain_result(str(exc))
            return
        result = await self._run(event, path)
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        rows = result.get("modules", [])[:25]
        lines = [f"道馆 {_plain(result.get('dojo', {}).get('name'), 60)} 的模块："]
        lines += [
            f"{i}. {_plain(item.get('name'), 50)} [{_display_id(item.get('id'))}]"
            for i, item in enumerate(rows, 1)
        ]
        yield event.plain_result("\n".join(lines) if rows else "暂无模块。")

    @pwn.command("题目")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def challenges(self, event: AstrMessageEvent, dojo: str, module: str):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        try:
            path = f"/dojos/{_id(dojo, dojo=True)}/modules/{_id(module)}/challenges"
        except PwnCollegeError as exc:
            yield event.plain_result(str(exc))
            return
        result = await self._run(event, path)
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        rows = result.get("challenges", [])[:30]
        lines = [f"模块 {_plain(result.get('module', {}).get('name'), 60)} 的题目："]
        lines += [
            f"{i}. {_plain(item.get('name'), 48)} [{_display_id(item.get('id'))}]"
            for i, item in enumerate(rows, 1)
        ]
        yield event.plain_result("\n".join(lines) if rows else "该模块目前没有公开题目。")

    @pwn.command("题面")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def description(self, event: AstrMessageEvent, dojo: str, module: str, challenge: str):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        try:
            path = (f"/dojos/{_id(dojo, dojo=True)}/modules/{_id(module)}"
                    f"/challenges/{_id(challenge)}")
        except PwnCollegeError as exc:
            yield event.plain_result(str(exc))
            return
        result = await self._run(event, path)
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        info = result.get("challenge", {})
        lines = [f"题目：{_plain(info.get('name'), 75)}", f"道馆：{_plain(result.get('dojo', {}).get('name'), 75)}",
                 f"模块：{_plain(result.get('module', {}).get('name'), 75)}", "题目描述：", _plain(info.get("description"), 1200) or "（无描述）"]
        yield event.plain_result("\n".join(lines))

    @pwn.command("排名")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def ranking(self, event: AstrMessageEvent, dojo: str, duration: int = 0):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        try:
            path = f"/dojos/{_id(dojo, dojo=True)}/rankings"
        except PwnCollegeError as exc:
            yield event.plain_result(str(exc))
            return
        if duration not in (0, 7, 30):
            yield event.plain_result("时长只支持 0（全部）、7（近七天）、30（近三十天）。")
            return
        result = await self._run(event, path, {"duration": duration})
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        yield event.plain_result(self._format_ranking(result, "道馆"))

    @pwn.command("模块排名")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.platform_adapter_type(
        filter.PlatformAdapterType.QQOFFICIAL | filter.PlatformAdapterType.QQOFFICIAL_WEBHOOK
    )
    async def module_ranking(self, event: AstrMessageEvent, dojo: str, module: str, duration: int = 0):
        event.stop_event()  # Prevent the normal LLM/browser pipeline from handling the command.
        try:
            path = f"/dojos/{_id(dojo, dojo=True)}/modules/{_id(module)}/rankings"
        except PwnCollegeError as exc:
            yield event.plain_result(str(exc))
            return
        if duration not in (0, 7, 30):
            yield event.plain_result("时长只支持 0、7、30。")
            return
        result = await self._run(event, path, {"duration": duration})
        if "_error" in result:
            yield event.plain_result(result["_error"])
            return
        yield event.plain_result(self._format_ranking(result, "模块"))

    @staticmethod
    def _format_ranking(result, kind):
        name = result.get("module", result.get("dojo", {})).get("name", "")
        names = {0: "全部", 7: "近七天", 30: "近三十天"}
        rows = result.get("standings", [])[:10]
        lines = [f"{kind}排名：{_plain(name, 70)}（{names.get(result.get('duration'), '全部')}）"]
        lines += [f"{int(r['rank'])}. {_plain(r['name'], 60)} — {int(r['solves'])} 题" for r in rows]
        return "\n".join(lines) if rows else "暂无排名数据。"
