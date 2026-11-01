# Explain the code: team guide

Forge can disqualify a team that cannot explain its work. Every member should be able to answer these without notes. Open each file and read it, and do not memorise this page.

## The flow

1. `app/wizard.py` asks four questions.
2. `app/rights.py` applies the rules and returns deadlines and amounts.
3. `app/clocks.py` draws the two countdowns from those numbers.
4. `streamlit_app.py` holds the page and the tools underneath.

## Questions judges may ask

**Where does AI decide things, and where does it not?**
The LLM reads the story, chooses the next tool and writes text (`app/orchestrator.py`, `app/agent.py`). It never decides a date, amount or eligibility. Those come from `app/rights.py`.

**What stops the AI making something up?**
`agent.fact_check` rejects any number that is not in the person's input or a tool result, and any promise of money. The orchestrator also refuses to finish until the rules engine has run.

**What makes it an agent, not a chatbot?**
The `run` loop in `app/orchestrator.py`: the LLM picks a tool, code validates and runs it, and the result goes back in. It stops at a question, a checked summary, or the step limit.

**What if the LLM is down?**
It raises `AgentError`, the screen says so, and the rules still work. See test 16 in `tests/test_hard_cases.py`.

**What happens to an OTP?**
`sanitize` in `app/safety.py` raises `SecretBlocked` before anything is stored or sent. Its known limit: a bare number with no label gets through.

**How do you know a rule is still current?**
`app/checks.py` fetches RBI's page and checks that the exact clause is there. It only says found after a successful check.

**How does the log detect tampering?**
Each entry's SHA-256 hash includes the previous hash (`append_event`, `chain_is_valid`), so changing an entry breaks the chain. It only lasts for the session, as there is no database yet.

**Why does the agent stop at the portal?**
The declaration, OTP, captcha and submit need the victim. A false complaint carries legal risk, so we never automate them.

**Why "preview"?**
The RBI directions start on 1 January 2027, so until then the clock shows how the rules will run.

**Did you use AI to build this?**
Yes, say so truthfully. Check first whether the organisers allow it.

## Before you submit

- Run `python -m pytest` and see the tests pass.
- Change one rule value in `app/rights.py`, see a test fail, and change it back.
- Each member should present the demo once.
