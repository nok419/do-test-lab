#!/usr/bin/env python3
"""Generate AUTH_USERS_JSON entries for the templates.

Usage:
  python tools/gen_user.py --username admin --role admin
  python tools/gen_user.py --username alice --role researcher
  python tools/gen_user.py --username bob --role assistant
  python tools/gen_user.py --username p001 --role participant

Outputs:
  - One JSON object (not a list). Wrap with [] for AUTH_USERS_JSON.

Notes:
  - The templates expect roles: admin / researcher / assistant / participant
  - Password is PBKDF2-HMAC-SHA256 hashed with per-user random salt.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys

PBKDF2_ITERATIONS = 200_000
PBKDF2_SALT_BYTES = 16
PBKDF2_DKLEN = 32  # 256-bit

ALLOWED_ROLES = ["admin", "researcher", "assistant", "participant"]

def pbkdf2_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_DKLEN,
    )

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", required=True)
    ap.add_argument("--role", required=True, choices=ALLOWED_ROLES)
    ap.add_argument("--password", default=None, help="If omitted, a random password is generated and printed.")
    args = ap.parse_args()

    password = args.password or secrets.token_urlsafe(16)
    salt = os.urandom(PBKDF2_SALT_BYTES)
    dk = pbkdf2_hash(password=password, salt=salt)

    out = {
        "username": args.username,
        "role": args.role,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "hash_b64": base64.b64encode(dk).decode("ascii"),
        "pbkdf2_iterations": PBKDF2_ITERATIONS,
    }

    print("# --- COPY BELOW ---")
    if args.password is None:
        print(f"# generated_password: {password}")
    print(json.dumps(out, ensure_ascii=False))
    print("# --- COPY ABOVE ---")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
