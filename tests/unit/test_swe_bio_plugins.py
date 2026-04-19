from pathlib import Path
from types import SimpleNamespace

import pytest

from kohakuterrarium.core.config import load_agent_config
from kohakuterrarium.modules.plugin.base import PluginBlockError, PluginContext

PLUGIN_DIR = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "agent-apps"
    / "swe_bio_agent"
    / "creatures"
    / "swe_bio_agent"
    / "custom"
)

import sys

if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from audit_plugin import AuditLoggerPlugin
from guard_plugin import RulesGuardPlugin


class DummyState(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class DummyStore:
    def __init__(self):
        self.state = DummyState()


class DummyContext(SimpleNamespace):
    pass


def make_plugin_context(tmp_path: Path) -> PluginContext:
    store = DummyStore()
    agent = SimpleNamespace(session_store=store)
    return PluginContext(
        agent_name="swe_bio_agent",
        working_dir=tmp_path,
        session_id="session-1",
        model="gpt-5.4",
        _agent=agent,
        _plugin_name="rules_guard",
    )


@pytest.mark.asyncio
async def test_rules_guard_blocks_mutation_before_read(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("repo rules", encoding="utf-8")
    plugin = RulesGuardPlugin()
    plugin_context = make_plugin_context(tmp_path)

    await plugin.on_load(plugin_context)

    with pytest.raises(PluginBlockError):
        await plugin.pre_tool_execute(
            {"path": "file.py", "content": "print('x')"},
            tool_name="write",
            context=DummyContext(
                path_guard=None, file_read_state=None, working_dir=tmp_path
            ),
        )


@pytest.mark.asyncio
async def test_rules_guard_allows_mutation_after_rule_read(tmp_path: Path):
    rules = tmp_path / "AGENTS.md"
    rules.write_text("repo rules", encoding="utf-8")
    plugin = RulesGuardPlugin()
    plugin_context = make_plugin_context(tmp_path)

    await plugin.on_load(plugin_context)
    read_context = DummyContext(
        path_guard=None, file_read_state=None, working_dir=tmp_path
    )
    successful = SimpleNamespace(error=None, output="ok")

    await plugin.post_tool_execute(
        successful,
        tool_name="read",
        args={"path": "AGENTS.md"},
        context=read_context,
        plugin_context=plugin_context,
    )

    result = await plugin.pre_tool_execute(
        {"path": "file.py", "content": "print('x')"},
        tool_name="write",
        context=read_context,
    )

    assert result is None


@pytest.mark.asyncio
async def test_rules_guard_blocks_dangerous_bash(tmp_path: Path):
    plugin = RulesGuardPlugin()
    plugin_context = make_plugin_context(tmp_path)

    await plugin.on_load(plugin_context)

    with pytest.raises(PluginBlockError):
        await plugin.pre_tool_execute(
            {"command": "git reset --hard"},
            tool_name="bash",
            context=DummyContext(
                path_guard=None, file_read_state=None, working_dir=tmp_path
            ),
        )


@pytest.mark.asyncio
async def test_audit_logger_writes_jsonl(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("repo rules", encoding="utf-8")
    log_dir = tmp_path / "audit"
    plugin = AuditLoggerPlugin(options={"log_dir": str(log_dir)})
    plugin_context = PluginContext(
        agent_name="swe_bio_agent",
        working_dir=tmp_path,
        session_id="session-1",
        model="gpt-5.4",
    )

    await plugin.on_load(plugin_context)
    await plugin.on_event(SimpleNamespace(type="user_input", content="请检查仓库规则"))
    await plugin.pre_tool_execute(
        {"path": "AGENTS.md"},
        tool_name="read",
        job_id="job-1",
        context=DummyContext(
            path_guard=None, file_read_state=None, working_dir=tmp_path
        ),
    )
    await plugin.post_tool_execute(
        SimpleNamespace(error=None, output="ok"),
        tool_name="read",
        job_id="job-1",
        args={"path": "AGENTS.md"},
        context=DummyContext(
            path_guard=None, file_read_state=None, working_dir=tmp_path
        ),
    )
    await plugin.on_agent_stop()
    await plugin.on_unload()

    files = list(log_dir.glob("*.jsonl"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "agent_start" in content
    assert "tool_start" in content
    assert "tool_end" in content


def test_swe_bio_agent_config_includes_humanizer_docs():
    config = load_agent_config("examples/agent-apps/swe_bio_agent/creatures/swe_bio_agent")
    names = [s.name for s in config.subagents]
    assert "humanizer_docs" in names
    humanizer = next(s for s in config.subagents if s.name == "humanizer_docs")
    assert humanizer.type == "custom"
    assert humanizer.module == "./custom/humanizer_docs.py"
    assert humanizer.config_name == "HUMANIZER_DOCS_CONFIG"
