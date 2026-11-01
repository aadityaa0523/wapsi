import json
from datetime import date

import httpx
import pytest

from app import agent, orchestrator

FACTS = {"txn": date(2027, 3, 1), "today": date(2027, 3, 2), "amount": 10000}
STATUS = {"sources": [{"clause_verified": True}]}


@pytest.fixture(autouse=True)
def llm_settings(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.test/v1")
    monkeypatch.setenv("LLM_MODEL", "test")
    monkeypatch.setenv("LLM_API_KEY", "key")


def scripted(*replies):
    queue = list(replies)

    def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(queue.pop(0))}}]})

    return httpx.MockTransport(handler)


def test_agent_chooses_tools_and_finishes_with_engine_dates():
    seen = []
    result = orchestrator.run(
        "I shared an OTP",
        FACTS,
        STATUS,
        seen.append,
        scripted(
            {"tool": "check_scam"},
            {"tool": "check_rules"},
            {"tool": "work_out_rights", "fault": "negligence"},
            {"tool": "finish", "summary": "Report to both by 06 Mar 2027."},
        ),
    )
    assert result["status"] == "done" and "06 Mar 2027" in result["text"]
    assert [step["tool"] for step in seen] == ["check_scam", "check_rules", "work_out_rights", "finish"]


def test_finish_without_rules_is_rejected_and_agent_recovers():
    result = orchestrator.run(
        "story",
        FACTS,
        STATUS,
        transport=scripted(
            {"tool": "finish", "summary": "All fine."},
            {"tool": "work_out_rights", "fault": "negligence"},
            {"tool": "finish", "summary": "Report to both."},
        ),
    )
    assert result["status"] == "done" and "rejected" in str(result["history"][0])


def test_invented_number_in_summary_is_rejected():
    with pytest.raises(agent.AgentError):
        orchestrator.run(
            "story",
            FACTS,
            STATUS,
            transport=scripted(
                {"tool": "work_out_rights", "fault": "negligence"},
                *[{"tool": "finish", "summary": "You will receive Rs 99999."}] * 5,
            ),
        )


def test_promise_in_summary_is_rejected():
    with pytest.raises(agent.AgentError):
        orchestrator.run(
            "story",
            FACTS,
            STATUS,
            transport=scripted(
                {"tool": "work_out_rights", "fault": "negligence"},
                *[{"tool": "finish", "summary": "Your refund is guaranteed."}] * 5,
            ),
        )


def test_agent_can_stop_and_ask():
    result = orchestrator.run("story", FACTS, STATUS, transport=scripted({"tool": "ask_person", "question": "Did you share an OTP?"}))
    assert result["status"] == "question"


def test_unknown_tool_and_bad_fault_do_not_crash():
    result = orchestrator.run(
        "story",
        FACTS,
        STATUS,
        transport=scripted(
            {"tool": "delete_everything"},
            {"tool": "work_out_rights", "fault": "promise_refund"},
            {"tool": "ask_person", "question": "Which applies?"},
        ),
    )
    assert "error" in result["history"][0]["result"] and "error" in result["history"][1]["result"]


def test_endless_tool_calls_stop_at_the_limit():
    with pytest.raises(agent.AgentError):
        orchestrator.run("story", FACTS, STATUS, transport=scripted(*[{"tool": "check_scam"}] * orchestrator.MAX_STEPS))


def test_missing_amount_is_reported_to_the_agent():
    result = orchestrator.work_out_rights({"fault": "negligence"}, FACTS | {"amount": None})
    assert "error" in result


def test_bad_ifsc_from_the_model_never_reaches_the_network():
    assert "error" in orchestrator.run_tool({"tool": "look_up_bank", "ifsc": "../secret"}, "", FACTS, STATUS)
