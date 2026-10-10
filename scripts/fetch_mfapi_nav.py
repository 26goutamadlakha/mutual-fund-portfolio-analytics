#!/usr/bin/env python3
"""Download and validate scheme NAV history from the public MFAPI endpoint.

Example:
  python scripts/fetch_mfapi_nav.py 119551 120503 --output data/real/nav.csv
The API response is external data: validate scheme names, history and provider terms.
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
import pandas as pd

BASE_URL = "https://api.mfapi.in/mf/"


def fetch_json(url: str, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "mf-portfolio-analytics/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_nav_response(payload: dict, requested_code: str):
    meta = payload.get("meta") or {}
    records = payload.get("data") or []
    scheme_code = str(meta.get("scheme_code") or requested_code)
    fund_name = str(meta.get("scheme_name") or requested_code)
    rows = []
    for item in records:
        date = pd.to_datetime(item.get("date"), format="%d-%m-%Y", errors="coerce")
        nav = pd.to_numeric(item.get("nav"), errors="coerce")
        if pd.isna(date) or pd.isna(nav) or nav <= 0:
            raise ValueError(f"Invalid NAV record for scheme {requested_code}: {item}")
        rows.append({"date": date.strftime("%Y-%m-%d"), "scheme_code": scheme_code,
                     "fund_name": fund_name, "nav": float(nav)})
    frame = pd.DataFrame(rows, columns=["date", "scheme_code", "fund_name", "nav"])
    if frame.empty:
        raise ValueError(f"No NAV observations returned for scheme {requested_code}.")
    if frame.duplicated(["date", "scheme_code"]).any():
        raise ValueError(f"Duplicate NAV dates returned for scheme {requested_code}.")
    frame = frame.sort_values("date").reset_index(drop=True)
    return meta, frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scheme_codes", nargs="+", help="One or more MFAPI scheme codes")
    parser.add_argument("--output", default="data/real/nav.csv", help="Destination CSV path")
    parser.add_argument("--pause", type=float, default=0.2, help="Pause between API requests in seconds")
    args = parser.parse_args()
    frames = []
    for idx, code in enumerate(args.scheme_codes):
        payload = fetch_json(BASE_URL + str(code))
        meta, frame = parse_nav_response(payload, str(code))
        print(f"{meta.get('scheme_code', code)} | {meta.get('scheme_name', 'Unknown')} | {len(frame)} rows")
        frames.append(frame)
        if idx + 1 < len(args.scheme_codes):
            time.sleep(max(args.pause, 0))
    combined = pd.concat(frames, ignore_index=True)
    if combined.duplicated(["date", "scheme_code"]).any():
        raise ValueError("Duplicate scheme/date combinations found after combining downloads.")
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(target, index=False)
    print(f"Wrote {len(combined)} validated NAV rows to {target}")


if __name__ == "__main__":
    main()
