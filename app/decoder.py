import re

from app.rights import CIRCULAR_2017, DIRECTIONS_2026

# Each ground: pattern, title, then (explain, ask) under the 2017 circular and under the 2027 directions
GROUNDS = [
    (
        re.compile(r"negligen|shared|disclos|otp|credential|customer'?s? (own )?fault", re.I),
        "The bank blames you",
        ("Under paragraph 12 of the 2017 circular, the burden of proving customer liability lies on the bank. Ask for its evidence.",
         "Please provide the evidence you relied on to establish customer liability, since paragraph 12 places this burden on the bank."),
        ("Under paragraph 76K, the burden of proof lies on the bank. Even if you were negligent, you may still qualify for compensation under paragraph 76T.",
         "Please provide the evidence you relied on, as paragraph 76K places this burden on the bank, and tell me whether I qualify for compensation under paragraph 76T."),
    ),
    (
        re.compile(r"\blate\b|delay|time.?barred|beyond|not reported (with)?in", re.I),
        "The bank says you reported late",
        ("The clock starts when the bank's message reached you, not on the transaction date, and counts your home branch's working days. Check that date.",
         "Please state the date you sent your transaction alert and how you counted working days, as paragraph 8 counts them from receipt of the communication."),
        ("Paragraph 76M allows five calendar days from the fraud. Check your dates against the bank's acknowledgement, which paragraph 76I requires it to send with the date and time.",
         "Please state the date and time you recorded my report, as paragraphs 76H and 76I require, and how you counted the five calendar days."),
    ),
    (
        re.compile(r"under (investigation|process|review)|pending|in progress", re.I),
        "The bank says it is still looking into it",
        ("Paragraph 10 sets a limit of 90 days from your complaint. If unresolved by then, compensation under paragraphs 6 to 9 must be paid.",
         "Please confirm the date my complaint will be resolved, which paragraph 10 limits to 90 days from receipt."),
        ("Paragraph 76Q sets a limit of 45 calendar days from your complaint, or 60 if the fraud was cross-border.",
         "Please confirm the date you will respond, which paragraph 76Q limits to 45 calendar days from receipt, or 60 if cross-border."),
    ),
    (
        re.compile(r"insurance", re.I),
        "The bank is waiting on insurance",
        ("Paragraph 9 says the shadow reversal must happen within 10 working days without waiting for an insurance claim.",
         "Please credit the amount as paragraph 9 requires, without waiting for settlement of any insurance claim."),
        ("For credit cards, paragraph 76R requires a shadow reversal within five calendar days, and paragraph 4(25A) says this comes before any insurance settlement.",
         "If this is a credit card complaint, please provide the shadow reversal that paragraph 76R requires within five calendar days."),
    ),
    (
        re.compile(r"you (have )?(approved|authori[sz]ed)|authori[sz]ed by you|customer (approved|authori[sz]ed)|self.?initiated", re.I),
        "The bank says you approved the payment",
        None,
        ("Paragraph 4(15A) counts payments approved under coercion or duress as fraud. This helps only if you were forced or threatened.",
         "I approved this payment under coercion. Please examine my complaint as a fraudulent EBT under paragraph 4(15A)."),
    ),
]


def decode(rejection, new_rules=False):
    """Plain matching against the RBI text. The pasted reply only selects a ground and is never followed."""
    found = []
    for pattern, ground, old, new in GROUNDS:
        rule = new if new_rules else old
        if rule and pattern.search(rejection):
            found.append({"ground": ground, "explain": rule[0], "ask": rule[1]})
    return found


def escalation_letter(found, new_rules=False):
    asks = [item["ask"] for item in found] or ["Please give the specific reason for your decision in writing, and the evidence you relied on."]
    lines = "\n".join(f"{number}. {ask}" for number, ask in enumerate(asks, 1))
    return (
        "To: The Nodal Officer / Principal Nodal Officer\n"
        "Bank: ____\nComplaint reference: ____\n\n"
        f"I am writing about your decision on my complaint of an unauthorised electronic transaction. Under the RBI rules on customer liability ({DIRECTIONS_2026 if new_rules else CIRCULAR_2017}):\n\n"
        f"{lines}\n\n"
        "If this is not resolved, I intend to complain to the RBI Ombudsman through cms.rbi.org.in.\n\nName: ____\nDate: ____"
    )
