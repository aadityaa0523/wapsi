from datetime import date, timedelta

NEW_REGIME = date(2027, 1, 1)
COMPENSATION_ENDS = date(2028, 1, 1)
CIRCULAR_2017 = "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040"
DIRECTIONS_2026 = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63011"

# Table 1 of the 2017 circular
LIABILITY_CAPS = {
    "Basic savings (BSBD)": 5000,
    "Other savings, prepaid, small current account, or credit card up to 5 lakh limit": 10000,
    "Other current account, or credit card above 5 lakh limit": 25000,
}
THIRD_PARTY, NEGLIGENCE, BANK_FAULT, AUTHORISED = "third_party", "negligence", "bank_fault", "authorised"


def add_working_days(start, days):
    # shortcut: skips Sundays only, so holidays make the real deadline later and never earlier; upgrade with a state holiday list
    current = start
    while days:
        current += timedelta(days=1)
        if current.weekday() != 6:
            days -= 1
    return current


def working_days_between(start, end):
    days = 0
    while add_working_days(start, days + 1) <= end:
        days += 1
    return days


def assess_2017(fault, loss, cap, alert, bank_report):
    result = {"regime": "2017 RBI circular", "source": CIRCULAR_2017, "verified_from": "RBI circular", "deadlines": {}}
    if fault == BANK_FAULT:
        return result | {"liability": 0, "summary": "Zero liability if the bank was at fault, whenever you report."}
    if fault == NEGLIGENCE:
        return result | {"liability": None, "summary": "You bear the loss until you report to the bank. The bank bears any loss after that, so report now."}
    if alert is None:
        return result | {"liability": None, "summary": "The clock starts when the bank's message reaches you. Enter that date to get your deadline."}
    result["deadlines"] = {"Zero liability": add_working_days(alert, 3), "Capped liability": add_working_days(alert, 7)}
    if bank_report is None:
        return result | {"liability": None, "summary": "Not reported to the bank yet."}
    waited = working_days_between(alert, bank_report)
    if waited <= 3:
        return result | {"liability": 0, "summary": "Reported in time for zero liability."}
    if waited <= 7:
        liability = min(loss, cap)
        return result | {"liability": liability, "summary": f"Reported late, so your liability per transaction is capped at Rs {liability:,}."}
    return result | {"liability": None, "summary": "Reported after 7 working days, so the bank's own board policy decides your liability."}


def assess_2027(txn, fault, loss, bank_report, police_report, used_before):
    deadline = txn + timedelta(days=5)
    result = {
        "regime": "RBI directions effective 1 Jan 2027",
        "source": DIRECTIONS_2026,
        "verified_from": "news summaries, RBI text not yet checked",
        "deadlines": {"Report to bank and police": deadline},
    }
    if fault == BANK_FAULT:
        return result | {"liability": None, "summary": "The outcome for bank fault under these rules is not confirmed yet. Report to both today."}
    if fault == THIRD_PARTY:
        in_time = bank_report is not None and bank_report <= deadline
        summary = "Reported in time for zero liability." if in_time else "Zero liability needs a bank report within 5 calendar days. After that, the bank's policy decides."
        return result | {"liability": 0 if in_time else None, "summary": summary}
    if txn >= COMPENSATION_ENDS:
        return result | {"liability": None, "compensation": 0, "summary": "Compensation covers frauds in the scheme's first year only."}
    # shortcut: uses the loss as entered, RBI says net loss; upgrade after reading the directions
    both = all(report is not None and report <= deadline for report in (bank_report, police_report))
    if used_before or loss > 50000:
        return result | {"liability": None, "compensation": 0, "summary": "Not eligible: compensation is once per lifetime and covers losses up to Rs 50,000."}
    possible = min(round(loss * 0.85), 25000)
    summary = f"Up to Rs {possible:,} possible, which the bank decides. It needs reports to BOTH the bank and police by {deadline:%d %b %Y}."
    return result | {"liability": None, "compensation": possible if both else 0, "possible": possible, "summary": summary}


def dual_report_guard(deadline, bank_report, police_report, today):
    warnings = []
    for name, report in (("bank", bank_report), ("police (1930 or cybercrime.gov.in)", police_report)):
        if report is None:
            left = (deadline - today).days
            warnings.append(f"No {name} report yet. " + (f"{left} day(s) left." if left >= 0 else "The deadline has passed. Report anyway."))
        elif report > deadline:
            warnings.append(f"The {name} report was after the deadline.")
    return warnings


def assess(txn, fault, loss, today, cap=10000, alert=None, bank_report=None, police_report=None, used_before=False):
    if loss <= 0 or today < txn:
        raise ValueError("Enter a loss above zero and a transaction date that is not in the future.")
    if fault == AUTHORISED:
        return {
            "regime": "Outside these rules", "source": None, "verified_from": None, "deadlines": {}, "liability": None, "warnings": [],
            "summary": "You approved this payment, so these RBI rules may not cover it. Still report it to 1930 and cybercrime.gov.in now.",
        }
    if txn < NEW_REGIME:
        return assess_2017(fault, loss, cap, alert, bank_report) | {"warnings": []}
    result = assess_2027(txn, fault, loss, bank_report, police_report, used_before)
    return result | {"warnings": dual_report_guard(result["deadlines"]["Report to bank and police"], bank_report, police_report, today)}
