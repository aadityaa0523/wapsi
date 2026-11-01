from datetime import date

from streamlit.testing.v1 import AppTest

from app import checks


def named(widgets, label):
    return next(widget for widget in widgets if widget.label == label)


TXN, LOSS, TOLD_BANK = "Date of the transaction", "Amount lost (Rs)", "Date you told the bank, if done"
FORM_BUTTON = "Check my rights"


def run_app(monkeypatch):
    async def fake_checks():
        return {"generated_at": "now", "sources": [], "database": {}}

    monkeypatch.setattr(checks, "run_checks", fake_checks)
    return AppTest.from_file("../streamlit_app.py", default_timeout=30).run()


def test_secret_is_blocked_and_not_logged(monkeypatch):
    app = run_app(monkeypatch)
    app.text_area[0].set_value("my otp is 482913").run()
    assert not app.exception
    assert "not saved" in app.warning[0].value
    assert "482913" not in str(app.session_state["audit"])


def test_ongoing_scam_tells_victim_to_hang_up(monkeypatch):
    app = run_app(monkeypatch)
    app.text_area[0].set_value("I am under digital arrest").run()
    assert any("Hang up" in error.value for error in app.error)


def test_form_shows_rights(monkeypatch):
    app = run_app(monkeypatch)
    named(app.date_input, TXN).set_value(date(2026, 10, 30))
    named(app.number_input, LOSS).set_value(5000)
    named(app.selectbox, "What best describes it?").set_value("I shared an OTP, PIN or password, or installed a bad app")
    named(app.button, FORM_BUTTON).click().run()
    assert not app.exception
    assert any("until you report" in info.value for info in app.info)


def test_preview_reaches_2027_rules_and_is_labelled(monkeypatch):
    app = run_app(monkeypatch)
    app.checkbox[0].check().run()
    named(app.date_input, TXN).set_value(date(2027, 3, 1))
    named(app.number_input, LOSS).set_value(10000)
    named(app.selectbox, "What best describes it?").set_value("I shared an OTP, PIN or password, or installed a bad app")
    named(app.date_input, TOLD_BANK).set_value(date(2027, 3, 1))
    named(app.button, FORM_BUTTON).click().run()
    assert not app.exception
    assert any("Preview with example dates" in warning.value for warning in app.warning)
    assert any("No police" in warning.value for warning in app.warning)


def test_preview_starts_on_the_new_rules(monkeypatch):
    app = run_app(monkeypatch)
    app.checkbox[0].check().run()
    assert named(app.date_input, TXN).value == date(2027, 1, 1)
    named(app.number_input, LOSS).set_value(10000)
    named(app.button, FORM_BUTTON).click().run()
    assert not app.exception
    assert any(header.value == "RBI directions effective 1 Jan 2027" for header in app.subheader)


def test_language_switch_translates_form_and_keeps_working(monkeypatch):
    app = run_app(monkeypatch)
    app.radio[0].set_value("हिन्दी").run()
    assert not app.exception
    assert app.text_area[0].label == "क्या हुआ? (वैकल्पिक)"
    named(app.number_input, "गई हुई राशि (रुपये)").set_value(5000)
    named(app.button, "मेरे अधिकार देखें").click().run()
    assert not app.exception


def test_impossible_dates_get_a_clear_message(monkeypatch):
    app = run_app(monkeypatch)
    named(app.date_input, TXN).set_value(date(2026, 10, 30))
    named(app.number_input, LOSS).set_value(5000)
    named(app.date_input, TOLD_BANK).set_value(date(2026, 10, 1))
    named(app.button, FORM_BUTTON).click().run()
    assert not app.exception
    assert any("cannot be before" in warning.value for warning in app.warning)


def test_recovery_checker_flags_a_fee(monkeypatch):
    app = run_app(monkeypatch)
    next(area for area in app.text_area if area.label == "The message").set_value("Pay a processing fee of Rs 5000").run()
    assert not app.exception
    assert any("warning sign" in error.value for error in app.error)


def test_several_transactions_show_the_safe_date(monkeypatch):
    app = run_app(monkeypatch)
    app.checkbox[0].check().run()
    next(radio for radio in app.radio if radio.label == "How many transactions?").set_value(2).run()
    by_label = lambda widgets, label: next(widget for widget in widgets if widget.label == label)
    by_label(app.date_input, "Transaction 1 date").set_value(date(2027, 3, 3))
    by_label(app.number_input, "Transaction 1 amount (Rs)").set_value(30000)
    by_label(app.date_input, "Transaction 2 date").set_value(date(2027, 3, 1))
    by_label(app.number_input, "Transaction 2 amount (Rs)").set_value(25000).run()
    assert not app.exception
    assert any("by 06 Mar 2027" in warning.value for warning in app.warning)
    assert any("above the Rs 50,000" in warning.value for warning in app.warning)


def through_questions(app, shared="Yes"):
    named(app.button, "No, it already happened").click().run()
    named(app.button, "Today").click().run()
    named(app.number_input, "How much did you lose? (Rs)").set_value(10000)
    named(app.button, "Continue").click().run()
    named(app.button, shared).click().run()
    return app


def test_guided_questions_reach_the_clocks_and_react(monkeypatch):
    app = through_questions(run_app(monkeypatch))
    assert not app.exception
    assert app.session_state["wizard"]["amount"] == 10000
    app.toggle[0].set_value(True).run()
    assert not app.exception


def test_on_a_call_goes_to_hang_up_first(monkeypatch):
    app = run_app(monkeypatch)
    named(app.button, "Yes, right now").click().run()
    assert any("Hang up" in error.value for error in app.error)
    named(app.button, "I have hung up").click().run()
    assert any("When did the money" in block.value for block in app.markdown)


def test_back_and_start_again(monkeypatch):
    app = run_app(monkeypatch)
    named(app.button, "No, it already happened").click().run()
    named(app.button, "Back").click().run()
    assert app.session_state["wizard"]["step"] == 0
    through_questions(app)
    named(app.button, "Start again").click().run()
    assert app.session_state["wizard"]["step"] == 0


def test_earlier_asks_how_many_days(monkeypatch):
    app = run_app(monkeypatch)
    named(app.button, "No, it already happened").click().run()
    named(app.button, "Earlier").click().run()
    named(app.number_input, "How many days ago?").set_value(9).run()
    named(app.button, "Continue").click().run()
    assert not app.exception and app.session_state["wizard"]["days_ago"] == 9


def test_my_deadline_is_prefilled_from_the_questions(monkeypatch):
    app = through_questions(run_app(monkeypatch))
    assert named(app.number_input, LOSS).value == 10000
    assert named(app.selectbox, "What best describes it?").value == "I shared an OTP, PIN or password, or installed a bad app"
    assert named(app.date_input, TXN).value == date(2027, 1, 1)
