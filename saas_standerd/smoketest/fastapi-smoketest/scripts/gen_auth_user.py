#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys


PBKDF2_ITERATIONS = 200_000
PBKDF2_SALT_BYTES = 16
PBKDF2_DKLEN = 32  # 256-bit


def pbkdf2_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_DKLEN,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Generate an auth user entry for AUTH_USERS_JSON")
    p.add_argument("--username", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--role", required=True, help="example: admin / researcher / participant")
    args = p.parse_args()

    salt = os.urandom(PBKDF2_SALT_BYTES)
    dk = pbkdf2_hash(args.password, salt)

    entry = {
        "username": args.username,
        "role": args.role,
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "hash_b64": base64.b64encode(dk).decode("ascii"),
        "pbkdf2_iterations": PBKDF2_ITERATIONS,
    }

    # 目的：
    # - 生成結果をそのまま AUTH_USERS_JSON の配列要素として貼り付けられるようにします
    json.dump(entry, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
