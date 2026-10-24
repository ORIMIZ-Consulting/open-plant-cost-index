"""Pull the OPCI series from FRED (Federal Reserve Economic Data) and keep cached snapshots.

The CSV download needs no API key. Set FRED_API_KEY to use the FRED API instead,
for heavier use.

Each snapshot is a folder data/snapshots/<pull date>/ holding:
  fred_raw.csv    long format: fred_id,date,value (monthly, as FRED gives it)
  manifest.json   pull time, method and coverage of each series

Run:  python -m opci.fred [--out data/snapshots]
"""
import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

from opci import checks, paths

SERIES_FILE = paths.ESCALATION_DIR / "series.yaml"
SNAPSHOT_DIR = paths.SNAPSHOT_DIR

CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
API_URL = "https://api.stlouisfed.org/fred/series/observations?{query}"
USER_AGENT = "opci (Open Plant Cost Index; https://github.com/ORIMIZ-Consulting/open-plant-cost-index)"
START_DATE = "2000-01-01"


class FredError(RuntimeError):
    pass


class FredOffline(FredError):
    """FRED could not be reached at all; the cached snapshot stays in use."""


def load_series_list(path=SERIES_FILE):
    return yaml.safe_load(Path(path).read_text())["series"]


def _get(url, timeout=60, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except Exception as exc:
            if attempt == tries:
                raise FredError(f"Could not reach FRED at {url}: {exc}") from exc
            time.sleep(2 * attempt)


def parse_csv(text, fred_id):
    """Parse a FRED graph CSV into [(date, value)]. Missing values ('.') are dropped."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 2:
        raise FredError(f"{fred_id}: empty or odd CSV from FRED")
    header = [h.strip() for h in rows[0]]
    if header[1] != fred_id:
        raise FredError(f"{fred_id}: CSV has column {header[1]!r}, expected {fred_id!r}")
    out = []
    for row in rows[1:]:
        if len(row) < 2 or row[1].strip() in ("", "."):
            continue
        out.append((row[0].strip(), float(row[1])))
    return out


def parse_api_json(text, fred_id):
    data = json.loads(text)
    if "observations" not in data:
        raise FredError(f"{fred_id}: FRED API error: {data.get('error_message', data)}")
    return [(o["date"], float(o["value"])) for o in data["observations"] if o["value"] != "."]


def fetch_series(fred_id, api_key=None):
    if api_key:
        query = urllib.parse.urlencode({
            "series_id": fred_id, "api_key": api_key,
            "file_type": "json", "observation_start": START_DATE,
        })
        return parse_api_json(_get(API_URL.format(query=query)), fred_id)
    obs = parse_csv(_get(CSV_URL.format(id=fred_id)), fred_id)
    return [(d, v) for d, v in obs if d >= START_DATE]


def _raw_csv(data):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["fred_id", "date", "value"])
    for fred_id, obs in data.items():
        for d, v in obs:
            w.writerow([fred_id, d, repr(v)])
    return buf.getvalue()


def write_snapshot(data, method, out_dir=SNAPSHOT_DIR, pulled_at=None):
    """Write {fred_id: [(date, value)]} as a snapshot folder. Returns the folder path.

    Snapshots are never overwritten. If the newest snapshot holds the same data, it is
    kept as is and returned. Otherwise a new folder is made, with a -2, -3 suffix when
    one already exists for the same day.
    """
    pulled_at = pulled_at or datetime.now(timezone.utc)
    raw = _raw_csv(data)
    try:
        newest = latest_snapshot(out_dir)
        if (newest / "fred_raw.csv").read_text(encoding="utf-8") == raw:
            return newest
    except (FredError, FileNotFoundError):
        pass
    day = pulled_at.strftime("%Y-%m-%d")
    folder, n = Path(out_dir) / day, 1
    while folder.exists():
        n += 1
        folder = Path(out_dir) / f"{day}-{n}"
    folder.mkdir(parents=True)
    (folder / "fred_raw.csv").write_text(raw, encoding="utf-8", newline="")
    manifest = {
        "pulled_at": pulled_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "BLS via FRED (Federal Reserve Bank of St. Louis)",
        "method": method,
        "series": {
            fred_id: {"first": obs[0][0], "last": obs[-1][0], "count": len(obs)}
            for fred_id, obs in data.items()
        },
        "data_to": min(obs[-1][0] for obs in data.values())[:7],
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return folder


def _snapshot_order(p):
    """Sort key: 2026-10-24 < 2026-10-24-2 < 2026-10-24-10 < 2026-11-20."""
    suffix = p.name[11:]
    return (p.name[:10], int(suffix) if suffix else 1)


def latest_snapshot(snapshot_dir=None):
    """Newest snapshot in `snapshot_dir`, or across the default folders (paths.snapshot_dirs)."""
    dirs = [Path(snapshot_dir)] if snapshot_dir else paths.snapshot_dirs()
    folders = sorted((p for d in dirs if d.exists() for p in d.iterdir() if (p / "manifest.json").exists()),
                     key=_snapshot_order)
    if not folders:
        raise FredError(f"No cached snapshot found in {', '.join(str(d) for d in dirs) or 'any folder'}")
    return folders[-1]


def load_snapshot(folder=None):
    """Return ({fred_id: [(date, value)]}, manifest) from a snapshot folder (default: latest)."""
    folder = Path(folder) if folder else latest_snapshot()
    data = {}
    with open(folder / "fred_raw.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data.setdefault(row["fred_id"], []).append((row["date"], float(row["value"])))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    return data, manifest


def pull_all(series_list=None, api_key=None):
    series_list = series_list or load_series_list()
    data, failed = {}, []
    for s in series_list:
        try:
            obs = fetch_series(s["fred_id"], api_key)
            if not obs:
                raise FredError(f"{s['fred_id']}: no observations")
            data[s["fred_id"]] = obs
            print(f"  {s['code']:<7}{s['fred_id']:<18}{obs[0][0]} to {obs[-1][0]}  ({len(obs)} months)")
        except FredError as exc:
            failed.append(s["fred_id"])
            print(f"  {s['code']:<7}FAILED: {exc}", file=sys.stderr)
    if failed and len(failed) == len(series_list):
        raise FredOffline("FRED could not be reached for any series.")
    if failed:
        raise FredError(
            "Series failed to download: " + ", ".join(failed)
            + ". If a series has been discontinued, add a replacement rule in escalation/series.yaml."
        )
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull OPCI series from FRED into a cached snapshot.")
    ap.add_argument("--out", default=None,
                    help="snapshot folder (default: data/snapshots in a clone, ~/.opci/snapshots after pip install)")
    ap.add_argument("--strict", action="store_true",
                    help="fail when FRED cannot be reached (used by the refresh Action)")
    args = ap.parse_args(argv)
    api_key = os.environ.get("FRED_API_KEY") or None
    method = "fred_api" if api_key else "fred_csv"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    explicit = args.out is not None
    args.out = Path(args.out) if explicit else paths.refresh_dir()
    try:
        # An explicit folder stands alone; by default compare with the newest snapshot anywhere.
        previous = latest_snapshot(args.out if explicit else None)
    except (FredError, FileNotFoundError):
        previous = None

    print(f"Pulling {len(load_series_list())} series from FRED ({method})")
    try:
        data = pull_all(api_key=api_key)
    except FredOffline as exc:
        if previous is None:
            print(f"ERROR: {exc} No cached snapshot to fall back on.", file=sys.stderr)
            return 1
        _, manifest = load_snapshot(previous)
        print(f"{exc} OPCI keeps using the cached snapshot {previous.name} "
              f"(data to {manifest['data_to']}).", file=sys.stderr)
        return 1 if args.strict else 0
    except FredError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Check 1 and 2: stale and discontinued series.
    stale = checks.stale_series(data, today)
    for s in stale:
        print(f"STALE: {s['fred_id']} has no new data since {s['last'][:7]} ({s['months']} months).")
    gone = [s for s in stale if s["discontinued"]]
    if gone:
        print("ERROR: possibly discontinued (no new data for more than "
              f"{checks.DISCONTINUED_MONTHS} months): " + ", ".join(s["fred_id"] for s in gone)
              + ". Add a replacement rule in escalation/series.yaml (see the pumps rule).", file=sys.stderr)
        return 1

    # Check 3: revisions since the last snapshot.
    revised = checks.revisions(load_snapshot(previous)[0], data) if previous else []
    for r in revised:
        print(f"REVISED: {r['fred_id']} {r['date'][:7]} {r['old']:g} -> {r['new']:g} ({r['change'] * 100:+.2f}%)")

    if previous is not None and (previous / "fred_raw.csv").read_text(encoding="utf-8") == _raw_csv(data):
        print(f"No change in data. Latest snapshot stays {previous.name}.")
        return 0
    folder = write_snapshot(data, method, args.out)
    report = {"checked_at": today, "previous_snapshot": previous.name if previous else None,
              "stale": stale, "revisions": revised}
    (folder / "refresh_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshot written to {folder} ({len(stale)} stale, {len(revised)} revised values).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
