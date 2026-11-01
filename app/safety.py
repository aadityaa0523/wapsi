import hashlib
import json
import re

SECRET_WORD = r"(otp|cvv|upi\s*pin|atm\s*pin|mpin|pin|password|passcode)"
SECRET = re.compile(rf"\b{SECRET_WORD}\b\W{{0,5}}(is\W{{0,3}})?\w*\d|\b\d{{3,8}}\b\W{{0,3}}(is\W{{0,3}})?(my\W{{0,3}})?{SECRET_WORD}\b", re.I)
MASKS = [
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I), "[PAN]"),
    (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7}\b"), "[CARD]"),
    (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "[AADHAAR]"),
    (re.compile(r"\b\d{9,18}\b"), "[ACCOUNT]"),
]
ONGOING = re.compile(r"digital arrest|still on (the )?(call|video)|(on|in) (a |the )?(video )?call (with|from)|told (me )?(to|not to) (pay|transfer|disconnect|tell)|keep(ing)? me on", re.I)
CRISIS = re.compile(r"kill myself|suicid|end my life|don'?t want to live|self[- ]harm", re.I)


class SecretBlocked(ValueError):
    pass


def sanitize(text):
    """Run before storing text or sending it anywhere. A bare number with no label can still get through."""
    if SECRET.search(text):
        raise SecretBlocked("Never share OTPs, PINs or passwords with anyone, including Wapsi. Your text was not saved.")
    for pattern, label in MASKS:
        text = pattern.sub(label, text)
    return text


def triage(text):
    """Most urgent first. Pasted text is only matched here, never followed as instructions."""
    if CRISIS.search(text):
        return "crisis"
    if ONGOING.search(text):
        return "ongoing"
    return "normal"


def append_event(log, event, at):
    previous = log[-1]["hash"] if log else "0" * 64
    entry = {"at": at, "event": event, "previous": previous}
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
    log.append(entry)
    return entry


def chain_is_valid(log):
    previous = "0" * 64
    for entry in log:
        body = {key: entry[key] for key in ("at", "event", "previous")}
        if entry["previous"] != previous or entry["hash"] != hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest():
            return False
        previous = entry["hash"]
    return True
