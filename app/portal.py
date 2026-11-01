import re

PORTAL_URL = "https://cybercrime.gov.in/"
MIN_DETAILS = 200
# The portal's own notice lists these as not allowed in incident details; straight quotes are removed to be safe
BANNED = re.compile(r"[#$@^*`’‘'\"~|!]")
STEPS = [
    "Open cybercrime.gov.in and click Register a Complaint.",
    "Read the declaration and click I Accept yourself. It says false information can make you liable, so check every detail first.",
    "Log in with your own mobile number, OTP and captcha. Wapsi never sees these.",
    "Fill in the details below, and upload your ID and evidence directly on the portal.",
    "Submit it yourself, then save the acknowledgement number.",
]
EVIDENCE = [
    "A copy of one national ID (Voter ID, Driving Licence, Passport, PAN or Aadhaar): jpeg, jpg or png, up to 5 MB. Upload it only on the portal, never to Wapsi.",
    "Evidence such as screenshots, SMS alerts and statements: up to 10 MB each.",
]


def clean_details(text):
    return re.sub(r"[ \t]{2,}", " ", BANNED.sub("", text)).strip()


def missing_items(details, bank, utr, amount):
    """What the portal's notice requires that is still missing. Checks the notice only, since the form sits behind login."""
    missing = []
    if len(details) < MIN_DETAILS:
        missing.append(f"Incident details need at least {MIN_DETAILS} characters. You have {len(details)}.")
    if re.search(r"\[(PAN|CARD|AADHAAR|ACCOUNT)\]", details):
        missing.append("Replace masked items such as [ACCOUNT] where the portal needs the real value.")
    if not bank.strip():
        missing.append("Name of the bank, wallet or merchant.")
    if not utr.strip():
        missing.append("Transaction ID or UTR number.")
    if not amount:
        missing.append("Fraud amount.")
    return missing


def kit_text(details, bank, utr, incident_date, incident_time, amount):
    fields = [
        f"Incident date and time: {incident_date} {incident_time}",
        f"Bank, wallet or merchant: {bank}",
        f"Transaction ID or UTR: {utr}",
        f"Date of transaction: {incident_date}",
        f"Fraud amount (Rs): {amount}",
        "",
        "Incident details:",
        details,
        "",
        "Still needed, for you to upload on the portal:",
        *EVIDENCE,
        "",
        "Steps:",
        *[f"{number}. {step}" for number, step in enumerate(STEPS, 1)],
    ]
    return "\n".join(fields)
