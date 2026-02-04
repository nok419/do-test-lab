#!/usr/bin/env python3
"""Generate secrets to paste into DigitalOcean App Platform environment variables.

Examples:
  python tools/gen_secret.py --bytes 32 --format hex
  python tools/gen_secret.py --bytes 32 --format urlsafe

Recommended:
  - AUTH_TOKEN_SECRET: urlsafe 32 bytes (or more)
"""

from __future__ import annotations

import argparse
import secrets
import base64

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bytes", type=int, default=32)
    ap.add_argument("--format", choices=["hex", "base64", "urlsafe"], default="urlsafe")
    args = ap.parse_args()

    raw = secrets.token_bytes(args.bytes)
    if args.format == "hex":
        print(raw.hex())
    elif args.format == "base64":
        print(base64.b64encode(raw).decode("ascii"))
    else:
        # urlsafe already returns str and includes enough entropy
        print(secrets.token_urlsafe(args.bytes))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
