from datetime import date, timedelta

import pytest

from app import rights
from app.rights import AUTHORISED, BANK_FAULT, COERCED, NEGLIGENCE, THIRD_PARTY, assess

MONDAY = date(2026, 6, 1)
NEW = date(2027, 3, 1)
LATER = NEW + timedelta(days=30)


def old(report_days, loss=50000, cap=10000):
    return assess(MONDAY, THIRD_PARTY, loss, LATER, cap=cap, alert=MONDAY, bank_report=rights.add_working_days(MONDAY, report_days))


def test_working_days_skip_sundays():
    assert rights.add_working_days(date(2026, 6, 5), 3) == date(2026, 6, 9)


@pytest.mark.parametrize("days, liability", [(3, 0), (4, 10000), (7, 10000), (8, None)])
def test_2017_third_party_boundaries(days, liability):
    assert old(days)["liability"] == liability


def test_2017_cap_never_exceeds_transaction():
    assert old(5, loss=2000)["liability"] == 2000


def test_2017_negligence_bears_loss_until_report():
    assert "until you report" in assess(MONDAY, NEGLIGENCE, 5000, LATER)["summary"]


def test_2017_bank_fault_is_zero_even_without_report():
    assert assess(MONDAY, BANK_FAULT, 5000, LATER)["liability"] == 0


def test_regime_switches_on_1_jan_2027():
    assert "2017" in assess(date(2026, 12, 31), NEGLIGENCE, 5000, LATER)["regime"]
    assert "2027" in assess(date(2027, 1, 1), NEGLIGENCE, 5000, LATER)["regime"]


def new(loss=10000, bank=0, police=0, txn=NEW, used_before=False):
    day = lambda offset: None if offset is None else txn + timedelta(days=offset)
    return assess(txn, NEGLIGENCE, loss, txn + timedelta(days=30), bank_report=day(bank), police_report=day(police), used_before=used_before)


def test_compensation_is_85_percent():
    assert new()["compensation"] == 8500


@pytest.mark.parametrize("bank, police", [(0, None), (None, 0), (6, 0), (0, 6)])
def test_missing_or_late_report_loses_compensation(bank, police):
    result = new(bank=bank, police=police)
    assert result["compensation"] == 0 and result["warnings"]


def test_day_5_counts_and_no_warning():
    result = new(bank=5, police=5)
    assert result["compensation"] == 8500 and not result["warnings"]


def test_loss_boundaries():
    assert new(loss=50000)["compensation"] == 25000
    assert new(loss=50001)["compensation"] == 0


def test_used_before_and_after_first_year_are_refused():
    assert new(used_before=True)["compensation"] == 0
    assert new(txn=date(2028, 1, 1))["compensation"] == 0


def test_authorised_payment_is_out_of_scope_but_told_to_report():
    result = assess(NEW, AUTHORISED, 5000, LATER)
    assert result["liability"] is None and "1930" in result["summary"]


@pytest.mark.parametrize("loss, today", [(0, LATER), (100, NEW - timedelta(days=1))])
def test_bad_input_is_refused(loss, today):
    with pytest.raises(ValueError):
        assess(NEW, NEGLIGENCE, loss, today)


def test_no_result_promises_a_refund():
    assert "refund" not in new()["summary"].lower()


def test_rbi_illustration_net_loss():
    result = assess(NEW, NEGLIGENCE, 40000, LATER, bank_report=NEW, police_report=NEW, recovered=15000)
    assert result["compensation"] == 21250


def test_gross_loss_decides_eligibility_not_net():
    result = assess(NEW, NEGLIGENCE, 60000, LATER, bank_report=NEW, police_report=NEW, recovered=20000)
    assert result["compensation"] == 0


def test_2027_bank_fault_is_zero_without_report():
    assert assess(NEW, BANK_FAULT, 5000, LATER)["liability"] == 0


def test_2027_third_party_needs_only_the_bank():
    result = assess(NEW, THIRD_PARTY, 5000, LATER, bank_report=NEW + timedelta(days=5))
    assert result["liability"] == 0 and not result["warnings"]
    assert assess(NEW, THIRD_PARTY, 5000, LATER, bank_report=NEW + timedelta(days=6))["liability"] is None


def test_2027_bank_response_deadline():
    result = assess(NEW, THIRD_PARTY, 5000, LATER, bank_report=NEW)
    assert result["deadlines"]["Bank must respond (60 days if cross-border)"] == NEW + timedelta(days=45)


def test_coerced_counts_only_under_new_rules():
    new_rules = assess(NEW, COERCED, 10000, LATER, bank_report=NEW, police_report=NEW)
    assert new_rules["compensation"] == 8500 and "4(15A)" in new_rules["summary"]
    assert assess(MONDAY, COERCED, 10000, LATER)["regime"] == "Outside these rules"


def test_recovered_above_loss_is_refused():
    with pytest.raises(ValueError):
        assess(NEW, NEGLIGENCE, 100, LATER, recovered=101)
