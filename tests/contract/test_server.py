import json
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
LIMIT = 12000
TOOLS = {"sw_status", "sw_summary", "sw_bom", "sw_audit", "sw_snapshot", "sw_set_properties",
         "sw_save", "sw_export", "sw_rename_document", "sw_add_component", "sw_create_drawing", "sw_background"}


def params():
    return StdioServerParameters(command=str(PY), args=[str(ROOT / "server.py")], env={**os.environ, "PYTHONUTF8": "1"})


async def test_tools_list_size_and_names():
    async with stdio_client(params()) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            names = {t.name for t in tools}
            assert names <= TOOLS, names - TOOLS
            total = sum(len(t.description or "") + len(json.dumps(t.input_schema)) for t in tools)
            assert total <= LIMIT, total


async def test_status_is_success_envelope():
    async with stdio_client(params()) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("sw_status", {})
            assert not res.is_error
            body = json.loads(res.content[0].text)
            assert body["ok"] is True and "connected" in body["data"]


async def test_bad_selector_is_tool_error():
    async with stdio_client(params()) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("sw_summary", {"doc": {"title": "__없는문서__.SLDPRT"}})
            assert res.is_error
            txt = res.content[0].text
            assert "DOC_NOT_FOUND" in txt or "SW_NOT_RUNNING" in txt


async def test_stdout_has_no_log_noise():
    """initialize 응답 전에 stdout에 프레임 아닌 바이트가 나오면 세션이 실패한다."""
    async with stdio_client(params()) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            assert init.server_info.name == "solidworks"
