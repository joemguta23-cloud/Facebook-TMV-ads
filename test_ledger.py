from datetime import date
import pytest
from ledger import Amendment

def test_owner_approved_oct8_amendment():
    a = Amendment(date(2026,10,8), "DAY", "52604039204627", 6276,600,6876,1000,6876)
    assert a.amendment_cents == 400
    assert a.new_lifetime_target_cents == 7276
    assert a.transaction_key == "TMV:2026-10-08:DAY:52604039204627:LIFETIME:7276"

def test_deterministic_duplicate_key():
    args=(date(2026,10,8), "DAY", "52604039204627", 6276,600,6876,1000,6876)
    assert Amendment(*args).transaction_key == Amendment(*args).transaction_key

def test_conflicting_live_target_rejected():
    with pytest.raises(ValueError):
        Amendment(date(2026,10,8),"DAY","52604039204627",6276,600,6876,1000,7276).validate()

def test_inconsistent_reservation_rejected():
    with pytest.raises(ValueError):
        Amendment(date(2026,10,8),"DAY","52604039204627",6276,600,6877,1000,6877).validate()
