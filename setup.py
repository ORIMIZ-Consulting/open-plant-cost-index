"""Build hook: bundle the repository data into the package.

A clone reads escalation/, location/, data/snapshots/ and data/releases/ from the
repository root. A wheel has no repository root, so the build copies those folders
into opci/_bundled/ (see opci/paths.py). All other settings are in pyproject.toml.
"""
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent
BUNDLE = ("escalation", "location", "data/snapshots", "data/releases")
SKIP = shutil.ignore_patterns("private_*", "__pycache__", "*.py", ".gitkeep")


class BuildWithData(build_py):
    def run(self):
        super().run()
        target = Path(self.build_lib) / "opci" / "_bundled"
        for rel in BUNDLE:
            src = ROOT / rel
            if src.exists():
                shutil.copytree(src, target / rel, ignore=SKIP, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithData})
