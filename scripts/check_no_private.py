"""Pre-commit check: block any staged file whose name starts with private_.

Files named private_* hold the user's licensed data (CEPCI or paid indices).
They must never be committed. Used by .pre-commit-config.yaml.
"""
import sys
from pathlib import Path


def main(paths):
    bad = [p for p in paths if Path(p).name.startswith("private_")]
    for p in bad:
        print(f"Blocked: {p} looks like licensed user data (private_*). Do not commit it.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
