"""Open Plant Cost Index (OPCI). Maintained by ORIMIZ Consulting."""

__version__ = "1.0.0rc1"
CREDIT = "Maintained by ORIMIZ Consulting"

from opci.api import combined, escalation, format_factor, series  # noqa: E402
from opci.locations import location  # noqa: E402


def read_release(name, freq="annual", investment="general", release_dir=None):
    """Read a pinned data release, e.g. read_release("data-2026-09"). See opci.release."""
    from opci import release   # imported here so `python -m opci.<module>` runs cleanly
    return release.read_release(name, freq, investment, release_dir or release.RELEASE_DIR)


__all__ = ["escalation", "location", "combined", "series", "format_factor", "read_release"]
