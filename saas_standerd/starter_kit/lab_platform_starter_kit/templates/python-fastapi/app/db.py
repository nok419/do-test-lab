from __future__ import annotations

import os
from typing import Tuple

import psycopg2


def try_db_ping() -> Tuple[bool, str]:
    # 注意：
    # - App Platformのビルド時にDB接続を要求すると失敗することがあるため、
    #   ここはランタイムでのみ使う前提です。
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return False, "DATABASE_URL is not set"

    try:
        # 実験用途では、接続チェックだけできれば十分なケースが多いので短時間でタイムアウトします。
        conn = psycopg2.connect(db_url, connect_timeout=3)
        conn.close()
        return True, "connected"
    except Exception as e:
        return False, f"db connection failed: {e}"
