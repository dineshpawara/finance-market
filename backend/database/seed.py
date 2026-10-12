"""
Standalone CLI Database Seeder
==============================
Usage:
    python -m database.seed
    or
    python database/seed.py
"""

import sys
from pathlib import Path

# Ensure backend root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.seed_service import seed_default_user

if __name__ == "__main__":
    print("[CLI] Starting idempotent database seed...", flush=True)
    user = seed_default_user()
    if user:
        print(f"[CLI] Successfully verified/seeded user: {user.email} (ID: {user.id})", flush=True)
    else:
        print("[CLI] Seeding completed.", flush=True)
