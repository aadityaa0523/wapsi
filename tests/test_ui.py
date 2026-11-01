from datetime import date

from streamlit.testing.v1 import AppTest

from app import checks


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
    app.date_input[0].set_value(date(2026, 10, 30))
    app.number_input[0].set_value(5000)
    app.selectbox[0].set_value("I shared an OTP, PIN or password, or installed a bad app")
    app.button[0].click().run()
    assert not app.exception
    assert any("until you report" in info.value for info in app.info)


def test_preview_reaches_2027_rules_and_is_labelled(monkeypatch):
    app = run_app(monkeypatch)
    app.checkbox[0].check().run()
    app.date_input[0].set_value(date(2027, 3, 1))
    app.number_input[0].set_value(10000)
    app.selectbox[0].set_value("I shared an OTP, PIN or password, or installed a bad app")
    app.date_input[2].set_value(date(2027, 3, 1))
    app.button[0].click().run()
    assert not app.exception
    assert any("Preview with example dates" in warning.value for warning in app.warning)
    assert any("No police" in warning.value for warning in app.warning)


def test_preview_starts_on_the_new_rules(monkeypatch):
    app = run_app(monkeypatch)
    app.checkbox[0].check().run()
    assert app.date_input[0].value == date(2027, 1, 1)
    app.number_input[0].set_value(10000)
    app.button[0].click().run()
    assert not app.exception
    assert any(header.value == "RBI directions effective 1 Jan 2027" for header in app.subheader)
