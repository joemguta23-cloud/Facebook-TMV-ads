"""Read-only TMV cloud staging service. Never writes to Meta."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify

app = Flask(__name__)
MELBOURNE = ZoneInfo('Australia/Melbourne')
LOS_ANGELES = ZoneInfo('America/Los_Angeles')


def window_for(now):
    local = now.astimezone(MELBOURNE)
    day = local.replace(hour=6, minute=0, second=0, microsecond=0)
    end = local.replace(hour=23, minute=0, second=0, microsecond=0)
    rollover = next((day.replace(hour=h) for h in range(6, 24) if day.replace(hour=h).astimezone(LOS_ANGELES).hour == 0), None)
    if rollover is None:
        raise RuntimeError('No LA midnight within approved operating hours')
    state = 'CLOSED'
    if day <= local < rollover:
        state = 'DAY'
    elif rollover <= local < end:
        state = 'EVENING'
    return {'melbourne_date': local.date().isoformat(), 'state': state, 'day_start': day.isoformat(), 'rollover': rollover.isoformat(), 'evening_end': end.isoformat()}


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'mode': 'READ_ONLY_STAGING', 'meta_writes_enabled': False, 'utc_observed': datetime.now(ZoneInfo('UTC')).isoformat()})


@app.get('/readiness')
def readiness():
    return jsonify({'status': 'NOT_READY_FOR_META_WRITES', 'reason': 'No approved Meta API credentials or durable transaction store configured', 'window': window_for(datetime.now(ZoneInfo('UTC')))})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '10000')))
