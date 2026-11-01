import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import streamlit as st

from app import agent, checks, decoder, rights
from app.safety import SecretBlocked, append_event, chain_is_valid, proof_pack, sanitize, triage

IST = timezone(timedelta(hours=5, minutes=30))
# shortcut: limit is per browser session, so a new session resets it; upgrade with a hosted rate limiter
MAX_AGENT_CALLS = 10
FAULTS = {
    "Money left without me sharing anything": rights.THIRD_PARTY,
    "I shared an OTP, PIN or password, or installed a bad app": rights.NEGLIGENCE,
    "I paid because I was threatened or forced, such as digital arrest": rights.COERCED,
    "The bank made a mistake": rights.BANK_FAULT,
    "I approved the payment myself, such as an investment scam": rights.AUTHORISED,
}


@st.cache_data(ttl=checks.CACHE_SECONDS, show_spinner="Checking official sources live")
def live_status():
    return asyncio.run(checks.run_checks())


@st.cache_data(ttl=checks.CACHE_SECONDS, show_spinner=False)
def live_rule_updates():
    return checks.rule_updates()


@st.cache_data(ttl=86400, show_spinner=False)
def bank_details(code):
    return checks.lookup_ifsc(code)


def log_event(event):
    audit = st.session_state.setdefault("audit", [])
    # Streamlit reruns the script on every click, so skip repeats
    if not audit or audit[-1]["event"] != event:
        append_event(audit, event, datetime.now(IST).isoformat())


def agent_call_allowed():
    used = st.session_state.get("agent_calls", 0)
    st.session_state["agent_calls"] = used + 1
    return used < MAX_AGENT_CALLS


st.set_page_config(page_title="Wapsi")
st.title("Wapsi")
st.write("**From 1 January 2027, reporting cyber fraud to only one place can cost you your compensation.** Wapsi tracks the bank route and the police route together, by the rules for your date, and keeps a record of each step.")
st.error("**Fraud in the last few hours? Call 1930 now and tell your bank.** Do this before anything else here.")
st.caption("Not legal advice. Wapsi cannot promise that you will get money back. Never share an OTP, PIN or password with anyone, including Wapsi.")

today = datetime.now(IST).date()
case_tab, rejected_tab, rules_tab = st.tabs(["My case", "Bank rejected me", "Live rules"])

with case_tab:
    story = st.text_area("What happened? (optional)", max_chars=4000)
    level = "normal"
    clean = None
    if story:
        try:
            clean = sanitize(story)
            level = triage(clean)
            log_event(f"Story checked, level: {level}")
        except SecretBlocked as blocked:
            st.warning(str(blocked))
            log_event("Blocked text containing a secret")

    if level == "crisis":
        st.error("You matter, and money can be dealt with later. Please call Tele-MANAS on 14416 now, at any hour.")
    if level == "ongoing":
        st.error("**Hang up now.** Police never arrest anyone over a video call, and no real officer asks you to pay. Do not send more money. Then call 1930.")

    if not agent.configured():
        st.info("The AI agent is off because no LLM key is set. The rules below still work.")
    else:
        st.caption("If you use the agent or get drafts, your story goes to an AI provider after your identifiers are masked. Leave the story empty to avoid this.")
    if agent.configured() and clean and level == "normal" and st.button("Let the agent read my story"):
        with st.status("Agent working") as steps:
            st.write("Checked your text for secrets and masked your identifiers.")
            try:
                if not agent_call_allowed():
                    raise agent.AgentError("LimitReached")
                st.session_state["classified"] = agent.classify(clean)
                st.write("Classified the fraud. Plain code, not the AI, decides your deadlines and amounts.")
                log_event("Agent classified the story")
                steps.update(state="complete")
            except agent.AgentError:
                st.session_state.pop("classified", None)
                log_event("Agent classification failed")
                steps.update(label="The agent is unavailable. Choose below and the rules will still work.", state="error")

    classified = st.session_state.get("classified")
    suggested = 0
    if classified:
        st.write(f"**Agent's reading:** {classified['fraud_type']} (confidence: {classified['confidence']}). Please check the choice below.")
        if classified["question"]:
            st.warning(classified["question"])
        if classified["fault"] in FAULTS.values():
            suggested = list(FAULTS.values()).index(classified["fault"])

    ifsc = st.text_input("Your branch IFSC (optional, finds your bank)", max_chars=11)
    bank = None
    if ifsc:
        try:
            bank = bank_details(ifsc)
            if bank:
                st.caption(f"{bank['bank']}, {bank['branch']}, {bank['city']}")
            else:
                st.warning("No branch found for that IFSC.")
        except ValueError as invalid:
            st.warning(str(invalid))
        except (httpx.HTTPError, KeyError):
            st.warning("The IFSC lookup is unavailable right now. You can continue without it.")

    with st.form("case"):
        txn = st.date_input("Date of the transaction", value=today, max_value=today)
        loss = st.number_input("Amount lost (Rs)", min_value=1, value=None, step=1)
        recovered = st.number_input("Amount already recovered (Rs)", min_value=0, value=0, step=1)
        fault = st.selectbox("What best describes it?", FAULTS, index=suggested)
        account = st.selectbox("Account type", rights.LIABILITY_CAPS)
        alert = st.date_input("Date the bank's message reached you, if any", value=None, max_value=today)
        bank_report = st.date_input("Date you reported to the bank, if done", value=None, max_value=today)
        police_report = st.date_input("Date you reported to 1930 or cybercrime.gov.in, if done", value=None, max_value=today)
        used_before = st.checkbox("I have received this RBI compensation before")
        submitted = st.form_submit_button("Check my rights")

    if submitted:
        if loss is None or recovered > loss:
            st.warning("Enter the amount lost, and a recovered amount no bigger than that.")
        else:
            result = rights.assess(txn, FAULTS[fault], int(loss), today, rights.LIABILITY_CAPS[account], alert, bank_report, police_report, used_before, int(recovered))
            log_event(f"Rights checked under: {result['regime']}")
            st.subheader(result["regime"])
            st.info(result["summary"])
            for warning in result["warnings"]:
                st.warning(warning)
            for name, deadline in result["deadlines"].items():
                st.metric(name, f"{deadline:%d %b %Y}", f"{(deadline - today).days} days left")
            if result["source"]:
                st.caption(f"Source: {result['source']} (checked against: {result['verified_from']}). Working-day dates are estimates because bank holidays vary by state.")
            if txn < rights.NEW_REGIME:
                st.caption("Rules change for transactions from 1 Jan 2027.")

            st.subheader("What to do next")
            for number, step in enumerate(rights.next_steps(txn, today, bank_report, police_report), 1):
                st.write(f"{number}. {step}")
            st.link_button("Report on cybercrime.gov.in", "https://cybercrime.gov.in/")

            facts = {
                "transaction_date": txn, "loss_rupees": int(loss), "recovered_rupees": int(recovered), "bank": bank["bank"] if bank else None, "ifsc": bank["ifsc"] if bank else None,
                "bank_alert": alert, "bank_report": bank_report, "police_report": police_report, "today": today,
            }
            if agent.configured() and clean and level == "normal":
                try:
                    if not agent_call_allowed():
                        raise agent.AgentError("LimitReached")
                    drafts = agent.draft_reports(clean, facts)
                    log_event("Agent drafts passed the fact check")
                    st.subheader("Drafts for you to check and send yourself")
                    st.text_area("Letter to your bank", drafts["bank_letter"], height=220)
                    st.text_area("Police complaint text", drafts["police_complaint"], height=220)
                except agent.AgentError as error:
                    log_event("Agent drafts were rejected or unavailable")
                    st.warning(f"No draft shown, because none could be verified. {error if 'fact check' in str(error) else ''}")

            st.download_button("Download my Proof Pack", proof_pack(facts, result, st.session_state["audit"]), "wapsi-proof-pack.txt", on_click="ignore")

with rejected_tab:
    st.write("Paste the bank's reply. Wapsi checks it against the RBI rules for your transaction date.")
    new_rules = st.checkbox("My transaction was on or after 1 January 2027")
    rejection = st.text_area("The bank's reply", max_chars=4000)
    if rejection:
        try:
            found = decoder.decode(sanitize(rejection), new_rules)
            log_event("Bank reply decoded")
            for item in found:
                st.write(f"**{item['ground']}.** {item['explain']}")
            if not found:
                st.write("No known reason matched. The letter below asks the bank to give its reason in writing.")
            st.text_area("Letter to send (check it and fill in the blanks)", decoder.escalation_letter(found, new_rules), height=300)
        except SecretBlocked as blocked:
            st.warning(str(blocked))

with rules_tab:
    status = live_status()
    st.caption(f"Sources checked at {status['generated_at']} UTC, refreshed every 5 minutes.")
    st.dataframe(
        [{"Source": s["name"], "Reachable": s["reachable"], "Rule clause found": str(s.get("clause_verified", "n/a")), "SHA-256": s.get("sha256", s.get("error", ""))} for s in status["sources"]],
        width="stretch",
    )
    st.subheader("Rule Watcher")
    try:
        updates = live_rule_updates()
        st.caption("Recent RBI press releases that may affect these rules. A person reviews them. Wapsi never changes a rule on its own.")
        for title in updates:
            st.text(title)
        if not updates:
            st.write("None in the current RBI feed.")
    except httpx.HTTPError:
        st.warning("The RBI feed could not be reached just now.")

if st.session_state.get("audit"):
    st.subheader("Tamper-evident log of this session")
    st.caption("Holds events only, never your story. Chain intact: " + str(chain_is_valid(st.session_state["audit"])))
    st.dataframe(st.session_state["audit"], width="stretch")
    if st.button("Delete my session data"):
        st.session_state.clear()
        st.rerun()
