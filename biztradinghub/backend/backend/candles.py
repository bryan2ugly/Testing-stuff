"""Public Coinbase 1-min BTC candle fetcher -- no API key needed."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import requests

COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
GRANULARITY_SECONDS = 60
MAX_CANDLES_PER_REQUEST = 300


def fetch_1m_candles(start: datetime, end: datetime, pause: float = 0.35) -> List[Tuple[datetime, float, float, float, float]]:
    """Returns a chronological list of (timestamp, open, high, low, close)."""
    candles = []
    chunk_span = timedelta(seconds=GRANULARITY_SECONDS * (MAX_CANDLES_PER_REQUEST - 1))
    cur_start = start
    session = requests.Session()

    while cur_start < end:
        cur_end = min(cur_start + chunk_span, end)
        params = {
            "start": cur_start.isoformat(),
            "end": cur_end.isoformat(),
            "granularity": GRANULARITY_SECONDS,
        }
        resp = session.get(COINBASE_CANDLES_URL, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(2.0)
            continue
        resp.raise_for_status()
        rows = resp.json()  # [time, low, high, open, close, volume], newest first
        for row in rows:
            ts = datetime.fromtimestamp(row[0], tz=timezone.utc)
            low, high, o, c = row[1], row[2], row[3], row[4]
            candles.append((ts, o, high, low, c))
        cur_start = cur_end
        time.sleep(pause)

    candles.sort(key=lambda r: r[0])
    seen = set()
    deduped = []
    for row in candles:
        if row[0] in seen:
            continue
        seen.add(row[0])
        deduped.append(row)
    return deduped


def fetch_1m_candles_with_volume(start: datetime, end: datetime, pause: float = 0.35):
    """Same as fetch_1m_candles, but also returns each bar's trade volume
    -- needed for the anchored-VWAP overlay. Returns (ts, o, h, l, c, volume)."""
    candles = []
    chunk_span = timedelta(seconds=GRANULARITY_SECONDS * (MAX_CANDLES_PER_REQUEST - 1))
    cur_start = start
    session = requests.Session()

    while cur_start < end:
        cur_end = min(cur_start + chunk_span, end)
        params = {
            "start": cur_start.isoformat(),
            "end": cur_end.isoformat(),
            "granularity": GRANULARITY_SECONDS,
        }
        resp = session.get(COINBASE_CANDLES_URL, params=params, timeout=15)
        if resp.status_code == 429:
            time.sleep(2.0)
            continue
        resp.raise_for_status()
        rows = resp.json()
        for row in rows:
            ts = datetime.fromtimestamp(row[0], tz=timezone.utc)
            low, high, o, c, vol = row[1], row[2], row[3], row[4], row[5]
            candles.append((ts, o, high, low, c, vol))
        cur_start = cur_end
        time.sleep(pause)

    candles.sort(key=lambda r: r[0])
    seen = set()
    deduped = []
    for row in candles:
        if row[0] in seen:
            continue
        seen.add(row[0])
        deduped.append(row)
    return deduped
