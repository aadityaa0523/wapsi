import re

from app.rights import CIRCULAR_2017

GROUNDS = [
    (
        re.compile(r"negligen|shared|disclos|otp|credential|customer'?s? (own )?fault", re.I),
        "The bank blames you",
        "Under paragraph 12 of the RBI circular, the burden of proving customer liability lies on the bank. Ask for the evidence it relied on.",
        "Please provide the evidence you relied on to establish customer liability, since paragraph 12 places this burden on the bank.",
    ),
    (
        re.compile(r"\blate\b|delay|time.?barred|beyond|not reported (with)?in", re.I),
        "The bank says you reported late",
        "The clock starts when the bank's communication reached you, not on the transaction date, and counts working days of your home branch. Check that date.",
        "Please state the date you sent your transaction alert and how you counted working days, as paragraph 8 counts them from receipt of the communication.",
    ),
    (
        re.compile(r"under (investigation|process|review)|pending|in progress", re.I),
        "The bank says it is still looking into it",
        "Paragraph 10 sets a limit of 90 days from your complaint. If unresolved by then, compensation under paragraphs 6 to 9 must be paid.",
        "Please confirm the date my complaint will be resolved, which paragraph 10 limits to 90 days from receipt.",
    ),
    (
        re.compile(r"insurance", re.I),
        "The bank is waiting on insurance",
        "Paragraph 9 says the shadow reversal must happen within 10 working days without waiting for an insurance claim.",
        "Please credit the amount as paragraph 9 requires, without waiting for settlement of any insurance claim.",
    ),
]


def decode(rejection):
    """Plain matching against the 2017 circular. The victim's text only selects a ground and is never followed."""
    return [{"ground": ground, "explain": explain, "ask": ask} for pattern, ground, explain, ask in GROUNDS if pattern.search(rejection)]


def escalation_letter(found):
    asks = [item["ask"] for item in found] or ["Please give the specific reason for your decision in writing, and the evidence you relied on."]
    lines = "\n".join(f"{number}. {ask}" for number, ask in enumerate(asks, 1))
    return (
        "To: The Nodal Officer / Principal Nodal Officer\n"
        "Bank: ____\nComplaint reference: ____\n\n"
        f"I am writing about your decision on my complaint of an unauthorised electronic transaction. Under the RBI circular on customer liability ({CIRCULAR_2017}):\n\n"
        f"{lines}\n\n"
        "If this is not resolved, I intend to complain to the RBI Ombudsman through cms.rbi.org.in.\n\nName: ____\nDate: ____"
    )
