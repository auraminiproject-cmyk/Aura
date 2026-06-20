#!/usr/bin/env python3
"""Weekly DB backup to local storage (replaces R2 backup in zero-card stack)."""

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "fashionai.db"
DEST_DIR = ROOT / "storage" / "backups"


def main() -> None:
    if not SRC.is_file():
        print("No SQLite DB at", SRC)
        return
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest = DEST_DIR / f"fashionai_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(SRC, dest)
    print("Backed up to", dest)


if __name__ == "__main__":
    main()
