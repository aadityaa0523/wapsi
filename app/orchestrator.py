import json

import httpx

from app import agent, checks, extras, rights

MAX_STEPS = 6
TOOLS = """Tools you may use, one per reply:
- {"tool": "check_scam"}: look for fake recovery-agent warning signs in the story.
- {"tool": "look_up_bank", "ifsc": "..."}: find the bank from an IFSC code that appears in the story.
- {"tool": "check_rules"}: confirm the RBI rule wording live on RBI's website.
- {"tool": "work_out_rights", "fault": "third_party" | "negligence" | "coerced" | "bank_fault" | "authorised"}: get deadlines and amounts from the rules engine.
- {"tool": "ask_person", "question": "..."}: ask one question if you cannot tell which fault applies, then stop.
- {"tool": "finish", "summary": "..."}: two plain sentences for the victim, then stop. Use only numbers and dates returned by tools.
Use work_out_rights before finish. Reply with one JSON object only."""


def check_rules(status):
    expected = [source for source in checks.SOURCES if "clause" in source]
    found = sum(1 for source in status["sources"] if source.get("clause_verified"))
    return {"clauses_expected": len(expected), "clauses_found": found}


def work_out_rights(step, facts):
    if step.get("fault") not in {rights.THIRD_PARTY, rights.NEGLIGENCE, rights.COERCED, rights.BANK_FAULT, rights.AUTHORISED}:
        return {"error": "unknown fault"}
    if not facts.get("amount"):
        return {"error": "the person has not entered the amount yet"}
    result = rights.assess(facts["txn"], step["fault"], facts["amount"], facts["today"], bank_report=facts.get("bank_report"), police_report=facts.get("police_report"))
    return {
        "rules": result["regime"],
        "summary": result["summary"],
        "deadlines": {name: f"{day:%d %b %Y}" for name, day in result["deadlines"].items()},
        "warnings": result["warnings"],
    }


def run_tool(step, story, facts, status):
    """The model only chooses. Each tool validates its input and runs in plain code."""
    name = step.get("tool")
    if name == "check_scam":
        return {"warning_signs": [item["flag"] for item in extras.recovery_flags(story)]}
    if name == "look_up_bank":
        try:
            return {"bank": checks.lookup_ifsc(str(step.get("ifsc", "")))}
        except (ValueError, KeyError, httpx.HTTPError) as error:
            return {"error": type(error).__name__}
    if name == "check_rules":
        return check_rules(status)
    if name == "work_out_rights":
        return work_out_rights(step, facts)
    return {"error": "unknown tool"}


def run(story, facts, status, on_step=lambda step: None, transport=None):
    """Plan, act, observe, repeat. Stops at a question, a checked summary or the step limit."""
    history = []
    used = set()
    tool_output = ""
    for _ in range(MAX_STEPS):
        prompt = f"{TOOLS}\nSteps so far: {json.dumps(history, default=str)}\n<story>{story}</story>"
        step = agent.ask_llm(prompt, transport)
        if not isinstance(step, dict):
            raise agent.AgentError("InvalidStep")
        name = step.get("tool")
        if name == "ask_person":
            on_step({"tool": name, "result": str(step.get("question", ""))[:300]})
            return {"status": "question", "text": str(step.get("question", ""))[:300], "history": history}
        if name == "finish":
            summary = str(step.get("summary", ""))[:800]
            # the agent may not finish without the rules, or with numbers no tool gave it
            if "work_out_rights" not in used or agent.fact_check(summary, tool_output + " " + story):
                history.append({"tool": "finish", "result": {"error": "Summary rejected. Use work_out_rights and only its numbers."}})
                on_step(history[-1])
                continue
            on_step({"tool": name, "result": summary})
            return {"status": "done", "text": summary, "history": history}
        result = run_tool(step, story, facts, status)
        if "error" not in result:
            used.add(name)
            tool_output += " " + json.dumps(result, default=str)
        history.append({"tool": name, "result": result})
        on_step(history[-1])
    raise agent.AgentError("StepLimit")
