import json
from types import SimpleNamespace as NS

from seller_agent.assistant import Assistant


class Scripted:
    """Stand-in for the Anthropic client: replays fixed responses."""
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        return self.responses.pop(0)


def tool_use(name, **inp):
    return NS(content=[NS(type="tool_use", id="t1", name=name, input=inp)])


def text(s):
    return NS(content=[NS(type="text", text=s)])


def test_tool_loop_returns_final_text():
    c = Scripted(tool_use("account_health"), text("All good."))
    a = Assistant(client=c)
    assert a.ask("how is my account?") == "All good."
    result = c.calls[1]["messages"][-2]["content"][0]
    assert result["type"] == "tool_result" and "order_defect_rate" in json.loads(result["content"])


def test_unknown_tool_and_bad_args_become_errors_not_crashes():
    c = Scripted(tool_use("drop_database"), text("n/a"))
    Assistant(client=c).ask("x")
    assert c.calls[1]["messages"][-2]["content"][0]["is_error"] is True


def test_assistant_has_no_approve_tool_and_write_tools_stay_pending():
    c = Scripted(tool_use("propose_refund", order_id="111-0000001-0000001", amount=1.0, reason="r"), text("done"))
    a = Assistant(client=c)
    a.ask("refund it")
    assert not any("approve" in n for n in a.tools)
    assert len(a.queue.pending()) == 1


def test_turn_limit():
    c = Scripted(*[tool_use("account_health") for _ in range(20)])
    assert "Stopped" in Assistant(client=c).ask("loop")
