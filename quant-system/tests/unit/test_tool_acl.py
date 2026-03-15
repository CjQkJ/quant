from apps.agent_orchestrator.permissions.tool_acl import ToolACL


def test_tool_acl():
    acl = ToolACL()
    assert acl.is_allowed("executor_agent", "run_paper_execution") is True
    assert acl.is_allowed("executor_agent", "set_kill_switch") is False

