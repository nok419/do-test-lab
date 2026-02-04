from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .auth import load_users, require_roles, sign_token, verify_password
from .db import try_db_ping
from .storage import generate_presigned_download_url, generate_presigned_upload_url

app = FastAPI(title="lab-fastapi-template")


class LoginRequest(BaseModel):
    username: str
    password: str
    # トークンの有効期限（秒）
    expires_in: int = 60 * 60


class SignedUploadRequest(BaseModel):
    # Spaces内のオブジェクトキー（例: "uploads/2026-01-01/sample.png"）
    key: str
    # content-type を固定したいときに指定します（任意）
    content_type: Optional[str] = None
    # URLの有効期限（秒）。実験用途では短めにして乱用耐性を上げます。
    expires_in: int = 300


@app.get("/", response_class=HTMLResponse)
def landing() -> str:
    # スモークテスト用の簡易ランディングページ。疎通確認の入口をまとめます。
    return """<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FastAPI Smoketest</title>
    <style>
      :root { color-scheme: light; }
      body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; margin: 0; background: #f7f7f7; color: #222; }
      main { max-width: 880px; margin: 48px auto; padding: 0 20px; }
      .card { background: #fff; border: 1px solid #e4e4e4; border-radius: 12px; padding: 20px; }
      h1 { font-size: 28px; margin: 0 0 8px; }
      h2 { font-size: 18px; margin: 24px 0 8px; }
      p { margin: 6px 0; line-height: 1.6; }
      code { background: #f1f1f1; padding: 2px 6px; border-radius: 6px; }
      ul { padding-left: 18px; margin: 8px 0; }
      .note { background: #f9f5e9; border: 1px solid #f0e2b6; padding: 12px; border-radius: 8px; }
    </style>
  </head>
  <body>
    <main>
      <div class="card">
        <h1>FastAPI Smoketest</h1>
        <p>このページはデプロイ確認用の簡易ランディングページです。</p>
        <div class="note">
          <p>最小の疎通確認は <code>/health</code> が 200 を返すことです。</p>
        </div>
        <h2>エンドポイント</h2>
        <ul>
          <li><code>/health</code> 監視用</li>
          <li><code>/health/db</code> データベース接続の確認（データベースが必要）</li>
          <li><code>/auth/login</code> 認証トークン発行</li>
          <li><code>/auth/me</code> 認証確認</li>
          <li><code>/signed-upload-url</code> 署名付きアップロードURL</li>
          <li><code>/signed-download-url</code> 署名付きダウンロードURL</li>
        </ul>
        <h2>補足</h2>
        <p><code>/auth/*</code> と署名URLは環境変数の設定が必要です。</p>
      </div>
    </main>
  </body>
</html>"""


@app.get("/health")
def health() -> dict:
    # 外形監視用。ここが200を返しているかだけを見る前提です。
    return {"ok": True}


@app.get("/health/db")
def health_db() -> dict:
    # DB接続の死活確認。実験中の障害切り分けで役立ちます。
    ok, detail = try_db_ping()
    if not ok:
        raise HTTPException(status_code=503, detail=detail)
    return {"ok": True, "detail": detail}


@app.post("/auth/login")
def login(req: LoginRequest) -> dict:
    # 注意：
    # - 研究室テンプレの最小実装です（AUTH_USERS_JSONでユーザ定義）
    # - AUTH_USERS_JSON は暗号化環境変数で管理することを推奨します
    users = load_users()
    u = users.get(req.username)
    if not u:
        raise HTTPException(status_code=401, detail="invalid credentials")

    salt_b64 = u.get("salt_b64")
    hash_b64 = u.get("hash_b64")
    role = u.get("role")
    if not salt_b64 or not hash_b64 or not role:
        raise HTTPException(status_code=500, detail="user entry is malformed")

    if not verify_password(req.password, salt_b64=salt_b64, hash_b64=hash_b64):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = sign_token(username=req.username, role=str(role), expires_in=req.expires_in)
    return {"token": token, "expires_in": req.expires_in, "role": role}


@app.get("/auth/me")
def me(user: dict = Depends(require_roles(["admin", "researcher", "assistant", "participant"]))) -> dict:
    # 認証できているかの確認用
    return {"ok": True, "user": user}


@app.post("/signed-upload-url")
def signed_upload_url(
    req: SignedUploadRequest,
    _user: dict = Depends(require_roles(["admin", "researcher", "assistant", "participant"])),
) -> dict:
    # 参加者が直接SpacesへPUTする方式にすると、アプリ帯域とアプリ負荷を節約できます。
    bucket = os.getenv("SPACES_BUCKET")
    if not bucket:
        raise HTTPException(status_code=500, detail="SPACES_BUCKET is not set")

    url = generate_presigned_upload_url(
        bucket=bucket,
        key=req.key,
        content_type=req.content_type,
        expires_in=req.expires_in,
    )
    return {"bucket": bucket, "key": req.key, "url": url, "expires_in": req.expires_in}


@app.get("/signed-download-url")
def signed_download_url(
    key: str,
    expires_in: int = 300,
    _user: dict = Depends(require_roles(["admin", "researcher", "assistant"])),
) -> dict:
    # デフォルトでは「研究者のみダウンロード可」に寄せています。
    # 参加者にも配布が必要な場合は、専用の公開バケット/公開prefixを使う等で設計してください。
    bucket = os.getenv("SPACES_BUCKET")
    if not bucket:
        raise HTTPException(status_code=500, detail="SPACES_BUCKET is not set")

    url = generate_presigned_download_url(bucket=bucket, key=key, expires_in=expires_in)
    return {"bucket": bucket, "key": key, "url": url, "expires_in": expires_in}
