from datetime import datetime
from zoneinfo import ZoneInfo
from app import app, window_for


def test_october_dst_rollover():
    local = ZoneInfo('Australia/Melbourne')
    w = window_for(datetime(2026, 10, 8, 18, 30, tzinfo=local))
    assert w['state'] == 'EVENING'
    assert w['rollover'].startswith('2026-10-08T18:00')


def test_day_and_night():
    local = ZoneInfo('Australia/Melbourne')
    assert window_for(datetime(2026, 10, 8, 9, 0, tzinfo=local))['state'] == 'DAY'
    assert window_for(datetime(2026, 10, 8, 23, 30, tzinfo=local))['state'] == 'CLOSED'


def test_no_writes():
    client = app.test_client()
    assert client.get('/health').json['meta_writes_enabled'] is False
    assert client.get('/readiness').json['status'] == 'NOT_READY_FOR_META_WRITES'
