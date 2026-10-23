"""Print the CHANGELOG.md section for a given version (used for release notes).

Usage: python tools/changelog_section.py 3.0.0
"""

from __future__ import annotations

import os
import re
import sys

CHANGELOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CHANGELOG.md")


def extract(version: str, text: str) -> str:
    match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: )", text, re.M | re.S)
    if not match:
        raise SystemExit(f"Version {version} not found in CHANGELOG.md")
    return match.group(1).strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
    with open(CHANGELOG, encoding="utf-8") as f:
        print(extract(sys.argv[1], f.read()))
