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
