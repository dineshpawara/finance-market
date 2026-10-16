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
    result = seed_default_user()
    if isinstance(result, tuple):
        user, raw_master_key = result
    else:
        user, raw_master_key = result, None

    if user:
        print(f"[CLI] Successfully verified/seeded user: {user.email} (ID: {user.id})", flush=True)
        if raw_master_key:
            print(f"[CLI] >>> MASTER RECOVERY KEY GENERATED: {raw_master_key} <<<", flush=True)
    else:
        print("[CLI] Seeding completed.", flush=True)
