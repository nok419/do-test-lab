from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import Depends, Header, HTTPException


# このテンプレは「研究室での運用の標準化」を優先し、
# 外部IdP（Auth0等）を前提にしない最小RBACを同梱します。
#
# 方針：
# - ユーザ一覧は AUTH_USERS_JSON（環境変数）で持つ
# - パスワードは平文で保持しない（pbkdf2でハッシュ化）
# - セッションはHMAC署名付きトークン（exp付き）で持つ
#
# 制約：
# - ユーザ追加は「ハッシュ生成 → 環境変数更新」が必要です
# - 大規模なユーザ管理が必要ならDB方式や外部IdPへ移行します


PBKDF2_ITERATIONS = 200_000
PBKDF2_SALT_BYTES = 16
PBKDF2_DKLEN = 32  # 256-bit


def _b64url_encode(raw: bytes) -> str:
    # JWT互換のbase64url（パディング無し）
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    # パディングを補ってデコード
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _get_secret() -> bytes:
    secret = os.getenv("AUTH_TOKEN_SECRET")
    if not secret:
        raise RuntimeError("AUTH_TOKEN_SECRET is not set")
    return secret.encode("utf-8")


def load_users() -> Dict[str, Dict[str, Any]]:
    raw = os.getenv("AUTH_USERS_JSON", "[]")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"AUTH_USERS_JSON must be valid JSON: {e}")

    if not isinstance(data, list):
        raise RuntimeError("AUTH_USERS_JSON must be a JSON array")

    users: Dict[str, Dict[str, Any]] = {}
    for u in data:
        if not isinstance(u, dict):
            continue
        username = u.get("username")
        if not username:
            continue
        users[str(username)] = u
    return users


def pbkdf2_hash(password: str, salt_b64: str) -> str:
    # salt_b64 は base64（標準）で保存します
    salt = base64.b64decode(salt_b64.encode("ascii"))
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_DKLEN,
    )
    return base64.b64encode(dk).decode("ascii")


def verify_password(password: str, salt_b64: str, hash_b64: str) -> bool:
    computed = pbkdf2_hash(password=password, salt_b64=salt_b64)
    # タイミング攻撃を避けるため、比較は一定時間にする
    return hmac.compare_digest(computed, hash_b64)


def sign_token(*, username: str, role: str, expires_in: int) -> str:
    exp = int(time.time()) + int(expires_in)
    payload = {"sub": username, "role": role, "exp": exp}

    payload_b = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_b64 = _b64url_encode(payload_b)

    mac = hmac.new(_get_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(mac)
    return f"{payload_b64}.{sig_b64}"


def verify_token(token: str) -> Dict[str, Any]:
    parts = token.split(".", 1)
    if len(parts) != 2:
        raise ValueError("token format is invalid")

    payload_b64, sig_b64 = parts
    expected = hmac.new(_get_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected), sig_b64):
        raise ValueError("signature mismatch")

    payload_raw = _b64url_decode(payload_b64)
    payload = json.loads(payload_raw.decode("utf-8"))

    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise ValueError("token expired")

    return payload


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")


def require_roles(allowed_roles: List[str]):
    def _dep(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = str(user.get("role", ""))
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return _dep
