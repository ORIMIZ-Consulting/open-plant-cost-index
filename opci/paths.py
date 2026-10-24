"""Where OPCI finds its data.

From a clone of the repository, the data are the repository folders:
escalation/, location/, data/snapshots/ and data/releases/.

From a pip install, the same folders are bundled inside the package at build time
(opci/_bundled/, see setup.py). Data the user makes later (opci refresh) go to a
user folder: OPCI_HOME, or ~/.opci by default.
"""
import os
from pathlib import Path

PKG = Path(__file__).resolve().parent
REPO = PKG.parent
IN_REPO = (REPO / "escalation" / "series.yaml").exists()
DATA_ROOT = REPO if IN_REPO else PKG / "_bundled"

ESCALATION_DIR = DATA_ROOT / "escalation"
LOCATION_DIR = DATA_ROOT / "location"
SNAPSHOT_DIR = DATA_ROOT / "data" / "snapshots"
RELEASE_DIR = DATA_ROOT / "data" / "releases"


def user_dir():
    return Path(os.environ.get("OPCI_HOME") or Path.home() / ".opci")


def refresh_dir():
    """Where `opci refresh` writes new snapshots."""
    return SNAPSHOT_DIR if IN_REPO else user_dir() / "snapshots"


def snapshot_dirs():
    """Folders searched for the latest snapshot: shipped data, then the user's own."""
    dirs = [SNAPSHOT_DIR]
    if not IN_REPO:
        dirs.append(user_dir() / "snapshots")
    return [d for d in dirs if d.exists()]


def output_dir():
    """Where maintainer outputs (VALIDATION.md, new releases) go."""
    return REPO if IN_REPO else Path.cwd()
