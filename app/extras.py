import hashlib
import re
from datetime import datetime, timedelta, timezone

MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
EVIDENCE_TYPES = ["jpg", "jpeg", "png", "pdf", "txt"]

RECOVERY_FLAGS = [
    (re.compile(r"\b(fee|charge|deposit|advance|processing|commission|tax|gst)\b.{0,40}\b(pay|send|transfer|rs\.?|rupees|₹)|\b(pay|send|transfer)\b.{0,40}\b(fee|charge|deposit|advance|processing|commission|tax|gst)\b|शुल्क|फीस|రుసుము", re.I | re.S), "Asks for a fee", "Do not pay. RBI's process and the police portal do not need you to pay a stranger to get your money back."),
    (re.compile(r"\b(otp|pin|password|cvv)\b|ओटीपी|ఓటీపీ", re.I), "Asks about your OTP, PIN or password", "Never share these with anyone, even if they say it is to return your money."),
    (re.compile(r"anydesk|teamviewer|quick ?support|rustdesk|screen ?shar|remote access|\.apk\b", re.I), "Asks you to install an app or share your screen", "Do not install it. This can give a stranger control of your phone."),
    (re.compile(r"guarantee|100\s?%|sure ?shot|assured|within \d+ hours|गारंटी|హామీ", re.I), "Promises a guaranteed recovery", "Nobody can guarantee this. Your bank and the police decide."),
    (re.compile(r"\b(rbi|cbi|police|cyber ?cell|i4c|court|judge|income tax|government)\b.{0,40}\b(officer|agent|official|department|recovery|refund)|recovery (agent|expert|specialist|officer)|hack(er)? .{0,20}(recover|back)|रिकवरी एजेंट", re.I | re.S), "Claims to be an official or a recovery expert", "Check independently. Call 1930 yourself and never use a number the caller gives you."),
    (re.compile(r"\burgent|immediately|today only|last chance|arrest|warrant|तुरंत|వెంటనే", re.I), "Pushes you to act immediately", "Pressure is a warning sign. Stop and call 1930 yourself."),
]


def recovery_flags(message):
    """Plain pattern checks on a message offering to get money back. A clean result does not prove it is safe."""
    return [{"flag": flag, "advice": advice} for pattern, flag, advice in RECOVERY_FLAGS if pattern.search(message)]


def fingerprint(content):
    return hashlib.sha256(content).hexdigest()


def evidence_event(content, file_type):
    """Only the hash, type and size are kept. The file and its name may hold personal data, so neither is stored."""
    return f"Evidence fingerprint {fingerprint(content)} ({file_type}, {len(content)} bytes)"


def _escape(text):
    return re.sub(r"([,;\\])", r"\\\1", str(text)).replace("\n", " ")


def calendar_file(deadlines, now=None):
    """iCalendar reminders for each deadline, each with an alarm a day before."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Wapsi//Deadlines//EN"]
    for number, (name, deadline) in enumerate(deadlines.items(), 1):
        lines += [
            "BEGIN:VEVENT",
            f"UID:wapsi-{stamp}-{number}@wapsi",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{deadline:%Y%m%d}",
            f"DTEND;VALUE=DATE:{deadline + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_escape('Wapsi: ' + name)}",
            f"DESCRIPTION:{_escape('Check this date with your bank. Helpline 1930. Wapsi never asks for an OTP or a fee.')}",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(name)}",
            "TRIGGER:-P1D",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
