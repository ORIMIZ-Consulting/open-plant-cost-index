"""OPCI public interface (spec sections 5 and 11): escalation, combined factor, series.

Escalation and location are reported apart, then the combined factor. Every result
carries the tool version, data date, investment type, productivity setting and
index source.
"""
import re
from pathlib import Path

from opci import CREDIT, __version__
from opci.calibrate import backtest
from opci.fred import latest_snapshot, load_snapshot, load_series_list
from opci.index import (DEFAULT_PRODUCTIVITY, SUPPLY_SHOCK_YEARS, compute,
                        supply_shock_warning)
from opci.locations import REFERENCE, location
from opci.overrides import OverrideError, load_override, override_path

INDEX_SOURCES = ("open", "private_cepci", "paid")
SCALES = ("cepci", "2019")
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
_PERIOD = re.compile(r"^(\d{4})(?:Q([1-4]))?$")


def parse_period(text):
    """'2011' -> ('annual', '2011'); '2011q2' -> ('quarterly', '2011Q2')."""
    m = _PERIOD.match(str(text).strip().upper())
    if not m:
        raise ValueError(f"Date {text!r} must be a year (2011) or a year and quarter (2011Q2)")
    return ("quarterly", f"{m[1]}Q{m[2]}") if m[2] else ("annual", m[1])


def _check_source(index_source):
    if index_source not in INDEX_SOURCES:
        raise ValueError(f"index_source must be one of {', '.join(INDEX_SOURCES)}")


def _open_source_note(snapshot):
    return f"BLS via FRED ({len(load_series_list())} series, cached snapshot {Path(snapshot).name})"


def _override_escalation(base, target, investment, productivity, index_source, paid_name, private_folder):
    """Escalation from the user's own override file. No gap filling, no scale."""
    path = override_path(index_source, paid_name, private_folder)
    values, freq, warnings = load_override(path)
    periods = sorted(values)
    target = target or periods[-1]
    picked = []
    for date, label in ((base, "base"), (target, "target")):
        kind, period = parse_period(date)
        if kind != freq:
            raise OverrideError(f"{path.name} holds {freq} values; the {label} date {date} is {kind}.")
        if period not in values:
            raise OverrideError(f"{path.name} has no value for the {label} date {period}. "
                                f"It covers {periods[0]} to {periods[-1]}. OPCI does not fill gaps.")
        picked.append(period)
    bp, tp = picked
    return {
        "factor": values[tp] / values[bp],
        "base": bp,
        "target": tp,
        "base_value": values[bp],
        "target_value": values[tp],
        "version": __version__,
        "credit": CREDIT,
        "data_to": periods[-1],
        "snapshot": None,
        "investment": investment,
        "productivity": productivity,
        "source": index_source,
        "source_file": path.name,
        "source_note": f"user override file {path.name} (the user's licensed data, not part of OPCI)",
        "scale": "override",
        "scale_2019": values.get("2019"),
        "flags": ["override"],
        "notes": warnings,
    }


def _anchor(scale, investment, productivity, snapshot):
    if scale not in SCALES:
        raise ValueError(f"scale must be one of {', '.join(SCALES)}")
    if scale == "2019":
        return 100.0
    return backtest(productivity=productivity, investment=investment, snapshot=snapshot)["anchor"]


def _table(freq, investment, productivity, anchor, snapshot):
    rows, manifest = compute(freq=freq, investment=investment, productivity=productivity,
                             anchor=anchor, snapshot=snapshot)
    return {r["period"]: r for r in rows}, manifest


def _part_note(row):
    """Plain label for a part period, e.g. '2026 is a part year (January to September average).'"""
    p, n = row["period"], row["months"]
    if "Q" in p:
        first = (int(p[-1]) - 1) * 3
        span = MONTHS[first] if n == 1 else f"{MONTHS[first]} to {MONTHS[first + n - 1]}"
        return f"{p} is a part quarter ({span} average)."
    span = MONTHS[0] if n == 1 else f"January to {MONTHS[n - 1]}"
    return f"{p} is a part year ({span} average)."


def _meta(manifest, snapshot, investment, productivity, index_source, scale, anchor):
    return {
        "version": __version__,
        "credit": CREDIT,
        "data_to": manifest["data_to"],
        "snapshot": Path(snapshot).name,
        "investment": investment,
        "productivity": productivity,
        "source": index_source,
        "scale": scale,
        "scale_2019": anchor,
    }


def latest_full_quarter(investment="general", snapshot=None):
    rows, _ = compute(freq="quarterly", investment=investment, anchor=1.0, snapshot=snapshot)
    return [r["period"] for r in rows if not r["part"]][-1]


def escalation(base, target=None, investment="general", productivity=DEFAULT_PRODUCTIVITY,
               index_source="open", scale="cepci", snapshot=None, paid_name=None, private_folder=None):
    """Escalation factor from the base date to the target date.

    base, target: '2011' or '2011Q2'. Target defaults to the latest full quarter
    (or the last period of an override file).
    productivity: rate on labour and engineering; 0 turns the adjustment off.
    index_source: 'open' (default), 'private_cepci' or 'paid' (see opci/overrides.py).
    """
    _check_source(index_source)
    if index_source != "open":
        return _override_escalation(base, target, investment, productivity, index_source,
                                    paid_name, private_folder)
    snapshot = Path(snapshot) if snapshot else latest_snapshot()
    target = target or latest_full_quarter(investment, snapshot)
    (bf, bp), (tf, tp) = parse_period(base), parse_period(target)
    anchor = _anchor(scale, investment, productivity, snapshot)
    tables, manifest = {}, None
    for freq in {bf, tf}:
        tables[freq], manifest = _table(freq, investment, productivity, anchor, snapshot)
    rows = []
    for freq, period, label in ((bf, bp, "base"), (tf, tp, "target")):
        if period not in tables[freq]:
            raise ValueError(f"No OPCI value for {label} date {period}. "
                             f"Data run from 2008 to {manifest['data_to']}.")
        rows.append(tables[freq][period])
    b, t = rows
    flags, notes = [], []
    for r in (b, t):
        if r["part"]:
            flags.append("part_year" if "Q" not in r["period"] else "part_quarter")
            notes.append(_part_note(r))
    shock = supply_shock_warning(bp, tp)
    if shock:
        flags.append("supply_shock")
        notes.append(shock)
    return {
        "factor": t["value"] / b["value"],
        "base": bp,
        "target": tp,
        "base_value": b["value"],
        "target_value": t["value"],
        **_meta(manifest, snapshot, investment, productivity, index_source, scale, anchor),
        "source_note": _open_source_note(snapshot),
        "flags": sorted(set(flags)),
        "notes": notes,
    }


def combined(base, target=None, to=REFERENCE, frm=REFERENCE, investment="general",
             productivity=DEFAULT_PRODUCTIVITY, index_source="open", scale="cepci", snapshot=None,
             paid_name=None, private_folder=None):
    """Escalation, location and the combined factor (escalation x location), reported apart."""
    esc = escalation(base, target, investment, productivity, index_source, scale, snapshot,
                     paid_name, private_folder)
    loc = location(to=to, frm=frm)
    return {
        "factor": esc["factor"] * loc["factor"],
        "low": esc["factor"] * loc["low"],
        "high": esc["factor"] * loc["high"],
        "escalation": esc,
        "location": loc,
    }


def series(start=2008, end=None, freq="annual", investment="general",
           productivity=DEFAULT_PRODUCTIVITY, index_source="open", scale="cepci", snapshot=None):
    """OPCI series as {'meta': {...}, 'rows': [...]}.

    Each row: period, value, part, supply_shock, and each component series rebased
    to 2019 = 100 (before the productivity adjustment). Open index only; an override
    file is used for factors, not republished as a series.
    """
    _check_source(index_source)
    if index_source != "open":
        raise ValueError("series() gives the open index only. Use escalation() or combined() "
                         "with an override file.")
    if freq not in ("annual", "quarterly"):
        raise ValueError("freq must be 'annual' or 'quarterly'")
    snapshot = Path(snapshot) if snapshot else latest_snapshot()
    anchor = _anchor(scale, investment, productivity, snapshot)
    rows, manifest = compute(freq=freq, investment=investment, productivity=productivity,
                             anchor=anchor, snapshot=snapshot, start=start, end=end)
    out = []
    for r in rows:
        out.append({
            "period": r["period"],
            "value": r["value"],
            "part": r["part"],
            "supply_shock": int(r["period"][:4]) in SUPPLY_SHOCK_YEARS,
            **{code: ratio * 100 for code, ratio in r["components"].items()},
        })
    meta = _meta(manifest, snapshot, investment, productivity, index_source, scale, anchor)
    meta["freq"] = freq
    meta["notes"] = [_part_note(r) for r in rows if r["part"]]
    return {"meta": meta, "rows": out}


def _setting_line(meta):
    if meta.get("source_file"):
        return (f"Data to {meta['data_to']} | index source: {meta['source']} "
                f"({meta['source_file']}) | productivity: not applied")
    prod = f"productivity {meta['productivity']:.1%}".replace(".0%", "%") if meta["productivity"] else "productivity off"
    return (f"Data to {meta['data_to']} | investment type: {meta['investment']} | {prod} | "
            f"index source: {meta['source']}")


def header(meta):
    return [f"Open Plant Cost Index (OPCI) v{meta['version']} | {meta['credit']}", _setting_line(meta)]


def format_factor(result):
    """Plain text block for a combined() or escalation() result (spec 5.1)."""
    esc = result.get("escalation", result)
    loc = result.get("location")
    lines = header(esc)
    lines.append(f"Escalation {esc['base']} to {esc['target']}:   x{esc['factor']:.2f}")
    sources = f"Sources: {esc['source_note']}"
    if loc:
        lines.append(f"Location {loc['frm_name']} to {loc['to_name']}:   x{loc['factor']:.2f}  "
                     f"(range {loc['low']:.2f} to {loc['high']:.2f}, confidence: {loc['confidence']})")
        lines.append(f"Combined factor:   x{result['factor']:.2f}")
        sources += f"; location: {loc['method']} (see location table, version {loc['location_version']})"
    lines.append(sources)
    lines += [f"Note: {n}" if not n.startswith("Note:") else n for n in esc["notes"]]
    return "\n".join(lines)
