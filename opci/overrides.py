"""Index overrides (spec section 9): the user's own CEPCI or paid index values.

Files live in the user's local folder, never in the repository:
  private_cepci.csv         the user's CEPCI subscription values
  private_paid_<name>.csv   paid data, for example private_paid_ucci.csv

Format: period,value (a header row is optional). Periods are years (2011) or
years and quarters (2011Q2), one kind per file. The tool checks for gaps and odd
jumps, says what the file covers and never fills gaps.

The folder is the current folder, or the folder named by OPCI_PRIVATE_DIR.
"""
import csv
import os
import re
from pathlib import Path

PRIVATE_DIR_ENV = "OPCI_PRIVATE_DIR"
JUMP_LIMIT = 0.25   # a change above 25% between periods is reported as an odd jump
_ANNUAL = re.compile(r"^\d{4}$")
_QUARTER = re.compile(r"^\d{4}Q[1-4]$")


class OverrideError(ValueError):
    pass


def private_dir(folder=None):
    return Path(folder or os.environ.get(PRIVATE_DIR_ENV) or Path.cwd())


def override_path(index_source, name=None, folder=None):
    """Path of the override file for an index source ('private_cepci' or 'paid')."""
    d = private_dir(folder)
    if index_source == "private_cepci":
        return d / "private_cepci.csv"
    if index_source != "paid":
        raise OverrideError(f"No override file for index source {index_source!r}")
    if name:
        return d / f"private_paid_{name}.csv"
    found = sorted(d.glob("private_paid_*.csv"))
    if len(found) == 1:
        return found[0]
    if not found:
        raise OverrideError(f"No private_paid_<name>.csv file found in {d}")
    raise OverrideError(f"Several paid files in {d}: {', '.join(p.name for p in found)}. "
                        "Name one with paid_name.")


def _next(period):
    if "Q" in period:
        y, q = int(period[:4]), int(period[-1])
        return f"{y + 1}Q1" if q == 4 else f"{y}Q{q + 1}"
    return str(int(period) + 1)


def load_override(path):
    """Return (values {period: value}, freq, warnings). Raises OverrideError on bad files."""
    path = Path(path)
    if not path.exists():
        raise OverrideError(f"Override file {path.name} not found in {path.parent}")
    values = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for n, row in enumerate(csv.reader(f), 1):
            if not row or not "".join(row).strip():
                continue
            if len(row) < 2:
                raise OverrideError(f"{path.name} line {n}: expected period,value")
            period, value = row[0].strip().upper(), row[1].strip()
            if n == 1 and period == "PERIOD":
                continue
            if not (_ANNUAL.match(period) or _QUARTER.match(period)):
                raise OverrideError(f"{path.name} line {n}: period {row[0]!r} must be like 2011 or 2011Q2")
            try:
                v = float(value)
            except ValueError:
                raise OverrideError(f"{path.name} line {n}: value {value!r} is not a number") from None
            if v <= 0:
                raise OverrideError(f"{path.name} line {n}: value must be above zero")
            if period in values:
                raise OverrideError(f"{path.name} line {n}: period {period} appears twice")
            values[period] = v
    if not values:
        raise OverrideError(f"{path.name} has no values")
    kinds = {"quarterly" if "Q" in p else "annual" for p in values}
    if len(kinds) > 1:
        raise OverrideError(f"{path.name} mixes years and quarters. Use one kind per file.")
    freq = kinds.pop()

    periods = sorted(values)
    warnings = [f"Override file {path.name} covers {periods[0]} to {periods[-1]} ({freq}). "
                "OPCI does not fill gaps or extend it."]
    missing, p = [], periods[0]
    while p != periods[-1]:
        p = _next(p)
        if p not in values:
            missing.append(p)
    if missing:
        warnings.append(f"Gaps in {path.name}: {', '.join(missing)}. Dates in the gaps cannot be used.")
    present = [p for p in periods]
    for a, b in zip(present, present[1:]):
        if _next(a) != b:
            continue
        change = values[b] / values[a] - 1
        if abs(change) > JUMP_LIMIT:
            warnings.append(f"Odd jump in {path.name}: {a} to {b} {change * 100:+.0f}%. Check the values.")
    return values, freq, warnings
