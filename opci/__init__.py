"""Open Plant Cost Index (OPCI). Maintained by ORIMIZ Consulting."""

__version__ = "0.1.0"
CREDIT = "Maintained by ORIMIZ Consulting"

from opci.api import combined, escalation, format_factor, series  # noqa: E402
from opci.locations import location  # noqa: E402
from opci.release import read_release  # noqa: E402

__all__ = ["escalation", "location", "combined", "series", "format_factor", "read_release"]
