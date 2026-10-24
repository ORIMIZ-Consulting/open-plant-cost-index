"""OPCI escalation calculation (METHOD section 6.3).

  OPCI(t) = Anchor x sum_i [ w_i x (P_i(t) / P_i(2019)) x adj_i(t) ]

  adj_i(t) = (1 - p)^(t - 2019) for labour and engineering, 1 for all others.

Annual values are the mean of the months. Quarterly values are the mean of the
three months. A period with fewer months than full is a part period and is flagged.
For quarters, t is the quarter midpoint measured from the 2019 midpoint, so
2019Q1 is -0.375 years and 2020Q1 is 0.625 years.
"""
import yaml

from opci import paths
from opci.fred import load_series_list, load_snapshot

BASE_YEAR = 2019
DEFAULT_PRODUCTIVITY = 0.02
PROTOTYPE_ANCHOR = 607.5   # public CEPCI 2019 annual average, used by the prototype

# Supply-shock years: left out of the scale fit, checked on a watch limit (METHOD.md).
SUPPLY_SHOCK_YEARS = (2021, 2022)
SUPPLY_SHOCK_NOTE = (
    "Note: 2021 and 2022 were unusual years. Supply shocks after the pandemic pushed "
    "equipment and material prices up quickly and unevenly. Index values for these years "
    "are less certain than for other years. Escalation from a 2021 or 2022 cost date may "
    "be somewhat overstated, and escalation to a 2021 or 2022 target date may be somewhat "
    "understated. See METHOD.md."
)


def supply_shock_warning(base, target):
    """Return the supply-shock note when the base or target date falls in 2021 or 2022, else None."""
    if any(int(str(d)[:4]) in SUPPLY_SHOCK_YEARS for d in (base, target)):
        return SUPPLY_SHOCK_NOTE
    return None


def load_weights(investment="general"):
    path = paths.ESCALATION_DIR / f"weights_{investment}.yaml"
    if not path.exists():
        raise ValueError(f"No weight set for investment type {investment!r}")
    data = yaml.safe_load(path.read_text())
    if data.get("status") != "reviewed":
        raise ValueError(f"Weight set {investment!r} is {data.get('status')!r}, not reviewed")
    total = sum(data["weights"].values())
    return {code: w / total for code, w in data["weights"].items()}


def _period_key(date, freq):
    year, month = int(date[:4]), int(date[5:7])
    if freq == "annual":
        return str(year)
    return f"{year}Q{(month - 1) // 3 + 1}"


def _months_in(freq):
    return 12 if freq == "annual" else 3


def _years_from_base(period):
    """Time from the 2019 midpoint to the period midpoint, in years."""
    if "Q" in period:
        year, q = period.split("Q")
        return int(year) + (int(q) - 0.5) / 4 - (BASE_YEAR + 0.5)
    return int(period) - BASE_YEAR


def average(obs, freq):
    """Mean of monthly observations by period. Returns {period: (mean, months)}."""
    groups = {}
    for date, value in obs:
        groups.setdefault(_period_key(date, freq), []).append(value)
    return {p: (sum(v) / len(v), len(v)) for p, v in sorted(groups.items())}


def compute(freq="annual", investment="general", productivity=DEFAULT_PRODUCTIVITY,
            anchor=PROTOTYPE_ANCHOR, snapshot=None, start=None, end=None):
    """Return the OPCI series as a list of dicts, one per period.

    Each row: period, value, months, part (bool), components {code: rebased ratio}.
    """
    data, manifest = load_snapshot(snapshot)
    weights = load_weights(investment)
    series = {s["code"]: s for s in load_series_list()}
    adjusted = {c for c, s in series.items() if s.get("productivity_adjusted")}

    averages, base = {}, {}
    for code in weights:
        obs = data[series[code]["fred_id"]]
        averages[code] = average(obs, freq)
        annual = average(obs, "annual")
        if str(BASE_YEAR) not in annual or annual[str(BASE_YEAR)][1] < 12:
            raise ValueError(f"{code}: no full {BASE_YEAR} data to rebase on")
        base[code] = annual[str(BASE_YEAR)][0]

    # Only periods where every series has data.
    periods = sorted(set.intersection(*(set(a) for a in averages.values())))
    if start is not None:
        periods = [p for p in periods if p[:4] >= str(start)]
    if end is not None:
        periods = [p for p in periods if p[:4] <= str(end)]

    rows = []
    for period in periods:
        months = min(averages[c][period][1] for c in weights)
        dt = _years_from_base(period)
        components, total = {}, 0.0
        for code, w in weights.items():
            ratio = averages[code][period][0] / base[code]
            components[code] = ratio
            adj = (1 - productivity) ** dt if code in adjusted else 1.0
            total += w * ratio * adj
        rows.append({
            "period": period,
            "value": anchor * total,
            "months": months,
            "part": months < _months_in(freq),
            "components": components,
        })
    return rows, manifest
