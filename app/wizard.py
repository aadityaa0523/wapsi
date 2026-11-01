from datetime import datetime, timedelta

import streamlit as st

from app import clocks, extras, rights
from app.i18n import TEXT

LAST_STEP = 4


def go(step, **answers):
    st.session_state["wizard"] = st.session_state.get("wizard", {}) | answers | {"step": step}
    st.rerun()


def clock_inputs(days_ago, today):
    """Before 2027 the rules are not in force, so the flow previews them as if the fraud happened on 1 January 2027."""
    preview = today < rights.NEW_REGIME
    if preview:
        return rights.NEW_REGIME, rights.NEW_REGIME + timedelta(days=days_ago), True
    return today - timedelta(days=days_ago), today, False


def seconds_left(txn, as_of, now):
    end = datetime.combine(txn + timedelta(days=rights.REPORT_DAYS + 1), datetime.min.time(), now.tzinfo)
    return (end - datetime.combine(as_of, now.time(), now.tzinfo)).total_seconds()


def next_action(required_police, told_bank, told_police):
    if not told_police and (required_police or told_bank):
        return "next_call"
    if not told_bank:
        return "next_bank"
    return "next_done" if told_police or required_police else "next_done_bank"


def run(language, now):
    t = lambda key: TEXT[key][language]
    answers = st.session_state.setdefault("wizard", {"step": 0})
    step = answers["step"]
    with st.container(key="wizard"):
        if step < LAST_STEP:
            dots = "".join(f'<i class="{"on" if number <= step else ""}"></i>' for number in range(LAST_STEP))
            st.markdown(f'<div class="wp-progress" role="img" aria-label="{t("step_of")} {step + 1} / {LAST_STEP}">{dots}<span>{t("step_of")} {step + 1} / {LAST_STEP}</span></div>', unsafe_allow_html=True)

        if step == 0:
            st.markdown(f'<h2 class="wp-q">{t("q_now")}</h2>', unsafe_allow_html=True)
            if answers.get("on_call"):
                st.error(t("hang_up"))
                st.markdown(f'<a class="wp-big" href="tel:1930">{t("call_1930")}</a>', unsafe_allow_html=True)
                if st.button(t("hung_up"), type="primary", width="stretch"):
                    go(1, on_call=False)
            else:
                yes, no = st.columns(2)
                if yes.button(t("q_now_yes"), width="stretch"):
                    go(0, on_call=True)
                if no.button(t("q_now_no"), type="primary", width="stretch"):
                    go(1)

        elif step == 1:
            st.markdown(f'<h2 class="wp-q">{t("q_when")}</h2>', unsafe_allow_html=True)
            first, second, third = st.columns(3)
            if first.button(t("today"), type="primary", width="stretch"):
                go(2, days_ago=0)
            if second.button(t("yesterday"), width="stretch"):
                go(2, days_ago=1)
            if third.button(t("earlier"), width="stretch") or answers.get("ask_days"):
                answers["ask_days"] = True
                days = st.number_input(t("days_ago"), min_value=2, max_value=3650, value=2, step=1)
                if st.button(t("continue"), type="primary", width="stretch"):
                    go(2, days_ago=int(days), ask_days=False)

        elif step == 2:
            st.markdown(f'<h2 class="wp-q">{t("q_amount")}</h2>', unsafe_allow_html=True)
            # a form takes the typed number and the click together, so one click is enough
            with st.form("wizard_amount", border=False):
                amount = st.number_input(t("set_amount"), min_value=1, value=answers.get("amount"), step=500, placeholder="₹", label_visibility="collapsed")
                sent = st.form_submit_button(t("continue"), type="primary", width="stretch")
            if sent and amount is None:
                st.warning(t("q_amount"))
            elif sent:
                go(3, amount=int(amount))

        elif step == 3:
            st.markdown(f'<h2 class="wp-q">{t("set_kind")}</h2>', unsafe_allow_html=True)
            yes, no, unsure = st.columns(3)
            if yes.button(t("yes"), width="stretch"):
                go(4, shared=True)
            if no.button(t("no"), width="stretch"):
                go(4, shared=False)
            # unsure takes the stricter path, so nobody misses a report they needed
            if unsure.button(t("not_sure"), width="stretch"):
                go(4, shared=True)

        if 0 < step < LAST_STEP and st.button(t("back")):
            go(step - 1)

    if step < LAST_STEP:
        return

    today = now.date()
    txn, as_of, preview = clock_inputs(answers["days_ago"], today)
    if txn < rights.NEW_REGIME:
        st.info(t("old_rules"))
    else:
        clock_area = st.container()
        bank_col, police_col = st.columns(2)
        told_bank = bank_col.toggle(t("set_bank"), key="clock_bank")
        told_police = police_col.toggle(t("set_police"), key="clock_police")
        state = rights.clock_state(txn, answers["amount"], answers["shared"], told_bank, told_police, seconds_left(txn, as_of, now), preview)
        with clock_area:
            clocks.show(state, language)
        action = next_action(answers["shared"], told_bank, told_police)
        if action == "next_call":
            st.markdown(f'<a class="wp-big" href="tel:1930">{t("call_1930")}</a>', unsafe_allow_html=True)
        else:
            st.success(t(action))
        deadline = {t("clock_title"): txn + timedelta(days=rights.REPORT_DAYS)}
        st.download_button(t("add_calendar"), extras.calendar_file(deadline), "wapsi-deadline.ics", "text/calendar", on_click="ignore", width="stretch")
    if st.button(t("start_over")):
        for key in ("wizard", "clock_bank", "clock_police"):
            st.session_state.pop(key, None)
        st.rerun()
