import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx
import streamlit as st

from app import agent, checks, decoder, extras, portal, rights, ui, wizard
from app.i18n import LANGUAGES, TEXT
from app.labels import FAULT_TEXT
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


st.set_page_config(page_title="Wapsi - Cyber Fraud Recovery Assistant", layout="wide")
ui.page_style()
language = st.session_state.get("language", LANGUAGES[0])
t = lambda key: TEXT[key][language]
ui.top_bar(language)
language_col, size_col = st.columns([3, 1])
language = language_col.radio("Language", LANGUAGES, horizontal=True, label_visibility="collapsed", key="language")
ui.text_size(size_col.segmented_control("Text size", list(ui.SIZES), default="A", label_visibility="collapsed"))
ui.brand(language)

today = datetime.now(IST).date()
now = datetime.now(IST)
wizard.run(language, now)
st.caption(t("disclaimer"))
ui.section(t("more_help"), "main")

case_tab, kit_tab, rejected_tab, shield_tab, rules_tab, judges_tab = st.tabs([t("tab_case"), t("tab_kit"), t("tab_rejected"), t("tab_shield"), t("tab_rules"), t("tab_judges")])

with case_tab:
    story = st.text_area(t("story"), max_chars=4000)
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
        st.error(TEXT["crisis"][language])
    if level == "ongoing":
        st.error(TEXT["hang_up"][language])

    if not agent.configured():
        st.info("The AI agent is off because no LLM key is set. The rules below still work.")
    else:
        st.checkbox(t("consent"), key="consent")
    agent_allowed = agent.configured() and clean and level == "normal" and st.session_state.get("consent")
    if agent_allowed and st.button("Let the agent read my story"):
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

    preview = st.checkbox("Preview the rules from 1 January 2027, using future dates", value=st.session_state.get("wizard", {}).get("step") == wizard.LAST_STEP and today < rights.NEW_REGIME)
    latest = date(2028, 12, 31) if preview else today

    with st.expander(t("optional_extras")):
        ifsc = st.text_input(t("ifsc"), max_chars=11)
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

        st.markdown("**More than one transaction or bank?**")
        st.caption("Add each one. Each has its own clock, so Wapsi shows the safest date for reporting them all.")
        count = st.radio("How many transactions?", [1, 2, 3, 4, 5], horizontal=True, key="transaction_count")
        rows = []
        for number in range(count if count > 1 else 0):
            day_col, amount_col, bank_col = st.columns(3)
            rows.append(
                {
                    "date": day_col.date_input(f"Transaction {number + 1} date", value=None, max_value=latest, key=f"row_date_{number}_{preview}"),
                    "amount": amount_col.number_input(f"Transaction {number + 1} amount (Rs)", min_value=1, value=None, step=1, key=f"row_amount_{number}"),
                    "bank": bank_col.text_input(f"Transaction {number + 1} bank or wallet", max_chars=60, key=f"row_bank_{number}"),
                }
            )
        plan = rights.plan_transactions(rows, max([today] + [row["date"] for row in rows if row["date"]]) if preview else today)
        if plan:
            st.write(f"**{plan['count']} transaction(s), Rs {plan['total']:,} in total.**")
            if plan["safe_deadline"]:
                st.warning(f"Report them all to your bank and police by {plan['safe_deadline']:%d %b %Y} ({plan['days_left']} days left). Each transaction has its own 5-day clock, and this is the earliest.")
            if plan["over_limit"]:
                st.warning("If these are one complaint, the total is above the Rs 50,000 compensation limit (paragraph 76T). Your bank decides how it treats them.")
            if plan["mixed_rules"]:
                st.warning("Some of these fall under the old rules and some under the new ones, so check each date in the form below.")
            if len(plan["banks"]) > 1:
                st.info(f"Report to each bank separately: {len(plan['banks'])} banks listed.")

        evidence = st.file_uploader("Fingerprint my evidence (optional)", type=extras.EVIDENCE_TYPES, accept_multiple_files=True, help="Wapsi keeps only a SHA-256 fingerprint, never the file. Add it to your Proof Pack to show that a file has not changed since now.")
        for item in evidence or []:
            if item.size > extras.MAX_EVIDENCE_BYTES:
                st.warning("One file is over 10 MB and was skipped.")
            else:
                event = extras.evidence_event(item.getvalue(), item.type)
                log_event(event)
                st.caption(event)

    guided = st.session_state.get("wizard", {})
    guided_done = guided.get("step") == wizard.LAST_STEP
    with st.form("case"):
        date_col, loss_col = st.columns(2)
        txn = date_col.date_input(t("txn"), value=rights.NEW_REGIME if preview else today, min_value=rights.NEW_REGIME if preview else date(2017, 7, 6), max_value=latest, key=f"txn_{preview}")
        loss = loss_col.number_input(t("loss"), min_value=1, value=guided.get("amount"), step=1)
        if guided_done:
            suggested = list(FAULTS.values()).index(rights.NEGLIGENCE if guided["shared"] else rights.THIRD_PARTY)
        fault = st.selectbox(t("fault"), FAULTS, index=suggested, format_func=lambda label: FAULT_TEXT[FAULTS[label]].get(language, label))
        bank_col, police_col = st.columns(2)
        bank_report = bank_col.date_input(t("reported_bank"), value=None, max_value=latest)
        police_report = police_col.date_input(t("reported_police"), value=None, max_value=latest)
        with st.expander(t("more_details")):
            recovered = st.number_input(t("recovered"), min_value=0, value=0, step=1)
            account = st.selectbox(t("account"), rights.LIABILITY_CAPS)
            alert = st.date_input(t("alert"), value=None, max_value=latest)
            used_before = st.checkbox(t("used_before"))
        submitted = st.form_submit_button(t("submit"))

    if submitted:
        # the 2027 rules cannot be reached with real dates yet, so preview counts from the dates entered
        as_of = max(today, txn, alert or txn, bank_report or txn, police_report or txn) if preview else today
        problem = rights.date_problem(txn, alert, bank_report, police_report)
        if loss is None or recovered > loss:
            st.warning("Enter the amount lost, and a recovered amount no bigger than that.")
        elif problem:
            st.warning(problem)
        else:
            result = rights.assess(txn, FAULTS[fault], int(loss), as_of, rights.LIABILITY_CAPS[account], alert, bank_report, police_report, used_before, int(recovered))
            log_event(f"Rights checked under: {result['regime']}")
            st.subheader(result["regime"])
            if preview:
                st.warning("Preview with example dates, not a real case. These rules start on 1 January 2027.")
            st.info(result["summary"])
            for warning in result["warnings"]:
                st.warning(warning)
            st.subheader(t("tracker"))
            ui.report_tracker(language, result["deadlines"], bank_report, police_report, as_of)
            if result["source"]:
                st.caption(f"Source: {result['source']} (checked against: {result['verified_from']}). Working-day dates are estimates because bank holidays vary by state.")
            if txn < rights.NEW_REGIME:
                st.caption("Rules change for transactions from 1 Jan 2027.")

            st.subheader(t("next"))
            for number, step in enumerate(rights.next_steps(txn, as_of, bank_report, police_report), 1):
                st.write(f"{number}. {step}")
            st.link_button("Report on cybercrime.gov.in", "https://cybercrime.gov.in/")
            if result["deadlines"]:
                st.download_button("Add deadlines to my calendar", extras.calendar_file(result["deadlines"]), "wapsi-deadlines.ics", "text/calendar", on_click="ignore")

            facts = {
                "transaction_date": txn, "loss_rupees": int(loss), "recovered_rupees": int(recovered), "bank": bank["bank"] if bank else None, "ifsc": bank["ifsc"] if bank else None,
                "bank_alert": alert, "bank_report": bank_report, "police_report": police_report, "checked_as_of": as_of,
            }
            if agent_allowed:
                try:
                    if not agent_call_allowed():
                        raise agent.AgentError("LimitReached")
                    drafts = agent.draft_reports(clean, facts)
                    log_event("Agent drafts passed the fact check")
                    st.session_state["police_draft"] = drafts["police_complaint"]
                    st.subheader("Drafts for you to check and send yourself")
                    st.text_area("Letter to your bank", drafts["bank_letter"], height=220)
                    st.text_area("Police complaint text", drafts["police_complaint"], height=220)
                except agent.AgentError as error:
                    log_event("Agent drafts were rejected or unavailable")
                    st.warning(f"No draft shown, because none could be verified. {error if 'fact check' in str(error) else ''}")

            st.download_button("Download my Proof Pack", proof_pack(facts, result, st.session_state["audit"]), "wapsi-proof-pack.txt", on_click="ignore")

with kit_tab:
    st.write("Everything the police portal's notice asks for, ready to copy. You accept its declaration, log in and submit yourself. Wapsi never files for you.")
    details = st.text_area("Incident details", value=st.session_state.get("police_draft") or clean or "", max_chars=4000, height=200)
    kit_bank = st.text_input("Bank, wallet or merchant", value=bank["bank"] if bank else "")
    utr = st.text_input("Transaction ID or UTR")
    kit_date = st.date_input("Incident date", value=today, max_value=today, key="kit_date")
    kit_time = st.time_input("Incident time", value=None)
    amount = st.number_input("Fraud amount (Rs)", min_value=0, value=0, step=1)
    try:
        cleaned = portal.clean_details(sanitize(details))
    except SecretBlocked as blocked:
        st.warning(str(blocked))
    else:
        if cleaned != details.strip():
            st.caption("Characters the portal does not allow were removed, and any card or account numbers were masked.")
        missing = portal.missing_items(cleaned, kit_bank, utr, amount)
        for item in missing:
            st.warning(item)
        if not missing:
            st.success("Ready, based on the portal's published notice. The form itself sits behind login, so it may ask for more.")
        kit = portal.kit_text(cleaned, kit_bank, utr, kit_date, kit_time or "____", amount)
        st.text_area("Your filing kit", kit, height=300)
        st.download_button("Download my filing kit", kit, "wapsi-filing-kit.txt", on_click="ignore")
        st.link_button("Open cybercrime.gov.in", portal.PORTAL_URL)

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

with shield_tab:
    st.write("Fake recovery agents target people who have just lost money. Paste a message or describe a call offering to get your money back.")
    offer = st.text_area("The message", max_chars=4000, key="recovery_message")
    if offer:
        try:
            flags = extras.recovery_flags(sanitize(offer))
        except SecretBlocked:
            flags = extras.recovery_flags("otp")
            st.warning("This contains an OTP, PIN or password. It was not saved. Never share these with anyone.")
        log_event(f"Recovery message checked, warning signs: {len(flags)}")
        if flags:
            st.error(f"{len(flags)} warning sign(s). Treat this as a likely scam, and call 1930 yourself.")
            for item in flags:
                st.write(f"**{item['flag']}.** {item['advice']}")
        else:
            st.info("No known warning signs found, but that does not make it safe. Never pay anyone to recover money, and call 1930 yourself to check.")

with rules_tab:
    status = live_status()
    ui.section(t("why"), "why")
    ui.two_report_table()
    ui.section(t("proof"), "proof")
    ui.stats(status)
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

with judges_tab:
    st.subheader("Why this matters")
    st.write("More than 65.89 lakh financial fraud complaints and more than Rs 55,050 crore reported on the national portal, 2021 to 2025, with more than Rs 8,189 crore marked as lien ([PIB, 21 July 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287039&reg=48&lang=2)). From 1 January 2027, compensation for small frauds needs reports to both the bank and the police route within five calendar days ([RBI, paragraph 76T](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0)).")
    st.write("**Other tools help you write a complaint. Wapsi protects your compensation.** We found no other tool that tracks both clocks using RBI's rules. The official portal and 1930 remain the only places to file.")
    st.subheader("Try it")
    st.write("A three-minute walk through the live app. No login needed.")
    for number, step in enumerate(
        [
            "Answer the four questions at the top. Then switch on I told my bank and watch the message change: one report is not enough.",
            "In Live rules, see how one missing report takes compensation to zero. In My deadline, tick Preview, enter any loss, choose the shared OTP option, and click Check my rights. Both clocks and warnings appear. Add one report date and run it again.",
            "In What happened, type: my otp is 482913. It is blocked and never logged.",
            "Replace it with: I am under digital arrest. The app tells the victim to hang up, in three languages.",
            "In Bank said no, paste: You shared your OTP so this is customer negligence. It cites the rule and writes the letter.",
            "In Live rules, compare the page hashes and clause results, which are fetched live from RBI.",
            "In Is this a scam?, paste: Pay a processing fee of Rs 5000 and I will guarantee your refund. It lists the warning signs.",
            "Download the calendar reminders and the Proof Pack, then click Delete my session data.",
        ],
        1,
    ):
        st.write(f"{number}. {step}")
    st.write("**Where it stops on purpose:** the portal's declaration, OTP, captcha and submit button are always left to the victim, because a false complaint carries legal risk.")
    st.write("**Known gaps:** the hard-case table, including what fails, is in the README: https://github.com/aadityaa0523/wapsi")

if st.session_state.get("audit"):
    st.subheader("Tamper-evident log of this session")
    st.caption("Holds events only, never your story. Chain intact: " + str(chain_is_valid(st.session_state["audit"])))
    st.dataframe(st.session_state["audit"], width="stretch")
    if st.button("Delete my session data"):
        st.session_state.clear()
        st.rerun()

ui.footer(language, f"{datetime.fromisoformat(status['generated_at']).astimezone(IST):%d %b %Y, %H:%M} IST" if status["generated_at"] != "now" else "")
