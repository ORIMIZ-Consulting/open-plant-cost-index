"""Checks run on every data refresh (spec section 8).

1. Stale series: no new data for more than 6 months. Reported.
2. Discontinued series: no new data for more than 12 months, or the download
   fails. The refresh fails and points to the replacement rule.
3. Revisions: a past value that changed by more than 0.5% since the last snapshot.
   Reported.
4. Back-test: run by opci.validate (fails above the 8% limit).
"""
STALE_MONTHS = 6
DISCONTINUED_MONTHS = 12
REVISION_LIMIT = 0.005


def _months_between(date, today):
    """Whole months from a YYYY-MM-DD observation to a YYYY-MM-DD day."""
    return (int(today[:4]) - int(date[:4])) * 12 + int(today[5:7]) - int(date[5:7])


def stale_series(data, today):
    """Series whose last observation is more than STALE_MONTHS before today."""
    out = []
    for fred_id, obs in data.items():
        months = _months_between(obs[-1][0], today)
        if months > STALE_MONTHS:
            out.append({"fred_id": fred_id, "last": obs[-1][0], "months": months,
                        "discontinued": months > DISCONTINUED_MONTHS})
    return out


def revisions(old, new, limit=REVISION_LIMIT):
    """Past values that changed by more than `limit` between two pulls."""
    out = []
    for fred_id, new_obs in new.items():
        before = dict(old.get(fred_id, []))
        for date, value in new_obs:
            if date in before and before[date]:
                change = value / before[date] - 1
                if abs(change) > limit:
                    out.append({"fred_id": fred_id, "date": date, "old": before[date],
                                "new": value, "change": change})
    return out
