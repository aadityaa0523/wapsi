from datetime import date, timedelta

NEW_REGIME = date(2027, 1, 1)
REPORT_DAYS = 5
EXAMPLE_LOSS = 10000
COMPENSATION_ENDS = date(2028, 1, 1)
CIRCULAR_2017 = "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11040"
DIRECTIONS_2026 = "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13543&Mode=0"

# Table 1 of the 2017 circular
LIABILITY_CAPS = {
    "Basic savings (BSBD)": 5000,
    "Other savings, prepaid, small current account, or credit card up to 5 lakh limit": 10000,
    "Other current account, or credit card above 5 lakh limit": 25000,
}
THIRD_PARTY, NEGLIGENCE, BANK_FAULT, AUTHORISED, COERCED = "third_party", "negligence", "bank_fault", "authorised", "coerced"


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


def assess_2027(txn, fault, loss, bank_report, police_report, used_before, recovered=0):
    deadline = txn + timedelta(days=REPORT_DAYS)
    result = {
        "regime": "RBI directions effective 1 Jan 2027",
        "source": DIRECTIONS_2026,
        "verified_from": "RBI directions, compared across all 7 bank types. Paragraph numbers shown are for commercial banks and differ for others",
        "deadlines": {},
    }
    if bank_report is not None:
        result["deadlines"] |= {
            "Bank must respond (60 days if cross-border)": bank_report + timedelta(days=45),
            "Credit cards only: shadow reversal": bank_report + timedelta(days=5),
        }
    if fault == BANK_FAULT:
        return result | {"liability": 0, "summary": "Zero liability and reversal if the bank was at fault, whether or not you report (paragraph 76L)."}
    if fault == THIRD_PARTY:
        result["deadlines"] = {"Report to bank": deadline} | result["deadlines"]
        in_time = bank_report is not None and bank_report <= deadline
        summary = "Reported in time for zero liability and reversal (paragraph 76M)." if in_time else "Zero liability needs a bank report within 5 calendar days of the fraud. After that, the bank's policy decides (paragraph 76M)."
        return result | {"liability": 0 if in_time else None, "summary": summary}
    result["deadlines"] = {"Report to bank AND police": deadline} | result["deadlines"]
    note = " RBI counts payments approved under coercion as fraud (paragraph 4(15A)), but your bank classifies the case." if fault == COERCED else ""
    if txn >= COMPENSATION_ENDS:
        return result | {"liability": None, "compensation": 0, "summary": "Compensation covers frauds in the scheme's first year only (paragraph 76U)." + note}
    both = all(report is not None and report <= deadline for report in (bank_report, police_report))
    if used_before or loss > 50000:
        return result | {"liability": None, "compensation": 0, "summary": "Not eligible: compensation is once per lifetime and covers gross losses up to Rs 50,000 (paragraph 76T)." + note}
    possible = min(round(max(loss - recovered, 0) * 0.85), 25000)
    summary = f"Up to Rs {possible:,} possible if your bank accepts the loss as genuine. It needs reports to BOTH the bank and police by {deadline:%d %b %Y} (paragraph 76T)." + note
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


def next_steps(txn, today, bank_report, police_report):
    """Most urgent first, so a recent victim acts before reading anything else."""
    steps = []
    if police_report is None:
        steps.append("Call 1930 now" + (" because money can sometimes still be stopped while the fraud is recent" if (today - txn).days <= 1 else "") + ", then file on cybercrime.gov.in. Save the acknowledgement number.")
    if bank_report is None:
        steps.append("Tell your bank through its official helpline and block the card or UPI. Then report in writing and keep the reference and date.")
    if bank_report is not None and police_report is not None:
        steps.append("Both reports are done. Keep the proof, and if the bank rejects you or goes silent, use the Bank rejected me tab.")
    steps.append("Save screenshots, SMS alerts and the scammer's numbers. Do not delete anything.")
    steps.append("Beware of anyone offering to recover your money for a fee. That is a common second scam.")
    return steps


def assess(txn, fault, loss, today, cap=10000, alert=None, bank_report=None, police_report=None, used_before=False, recovered=0):
    if loss <= 0 or today < txn or not 0 <= recovered <= loss:
        raise ValueError("Enter a loss above zero, a recovered amount no bigger than the loss, and a date that is not in the future.")
    if fault == AUTHORISED or (fault == COERCED and txn < NEW_REGIME):
        return {
            "regime": "Outside these rules", "source": None, "verified_from": None, "deadlines": {}, "liability": None, "warnings": [],
            "summary": "You approved this payment, so these RBI rules may not cover it. Under the rules from 2027, a payment forced by threats can count as fraud. Still report it to 1930 and cybercrime.gov.in now.",
        }
    if txn < NEW_REGIME:
        result = assess_2017(fault, loss, cap, alert, bank_report)
        if bank_report is not None:
            result["deadlines"] |= {"Bank must credit the amount back (shadow reversal)": add_working_days(bank_report, 10), "Bank must resolve your complaint": bank_report + timedelta(days=90)}
        return result | {"warnings": []}
    result = assess_2027(txn, fault, loss, bank_report, police_report, used_before, recovered)
    needs_both = fault in (NEGLIGENCE, COERCED)
    return result | {"warnings": dual_report_guard(txn + timedelta(days=REPORT_DAYS), bank_report, police_report, today) if needs_both else []}


def two_report_scenarios():
    """Example cases run through the real engine, so the table changes if the rules do."""
    txn = NEW_REGIME
    as_of = txn + timedelta(days=30)
    day = lambda count: None if count is None else txn + timedelta(days=count)
    cases = [
        ("Bank and police, both within 5 days", 5, 5),
        ("Bank only, on the same day", 0, None),
        ("Police only, on the same day", None, 0),
        ("Police on day 1, but bank on day 6", 6, 1),
    ]
    return [(name, assess(txn, NEGLIGENCE, EXAMPLE_LOSS, as_of, bank_report=day(bank), police_report=day(police))["compensation"]) for name, bank, police in cases]
