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
      main { max-width: 980px; margin: 48px auto; padding: 0 20px 64px; }
      .card { background: #fff; border: 1px solid #e4e4e4; border-radius: 12px; padding: 20px; }
      h1 { font-size: 28px; margin: 0 0 8px; }
      h2 { font-size: 18px; margin: 24px 0 8px; }
      h3 { font-size: 16px; margin: 0 0 8px; }
      p { margin: 6px 0; line-height: 1.6; }
      code { background: #f1f1f1; padding: 2px 6px; border-radius: 6px; }
      ul { padding-left: 18px; margin: 8px 0; }
      .note { background: #f9f5e9; border: 1px solid #f0e2b6; padding: 12px; border-radius: 8px; }
      .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); margin-top: 12px; }
      .panel { border: 1px solid #e7e7e7; border-radius: 12px; padding: 16px; background: #fbfbfb; }
      .field { display: grid; gap: 6px; margin-bottom: 10px; }
      label { font-size: 13px; color: #444; }
      input, select, textarea { font: inherit; padding: 8px 10px; border-radius: 8px; border: 1px solid #d5d5d5; background: #fff; }
      button { font: inherit; padding: 8px 12px; border-radius: 8px; border: 1px solid #3a3a3a; background: #222; color: #fff; cursor: pointer; }
      button.secondary { background: #fff; color: #222; }
      .row { display: flex; gap: 8px; flex-wrap: wrap; }
      .output { background: #111; color: #e8e8e8; padding: 10px; border-radius: 8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; min-height: 72px; white-space: pre-wrap; }
      .hint { font-size: 12px; color: #666; }
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
        <h2>動作チェックUI</h2>
        <p>同一オリジンでの簡易確認を想定しています。認証が必要なAPIはトークンを設定してください。</p>
        <div class="grid">
          <section class="panel">
            <h3>health</h3>
            <p class="hint">GET /health</p>
            <div class="row">
              <button type="button" id="btn-health">実行</button>
            </div>
            <div class="output" id="out-health"></div>
          </section>
          <section class="panel">
            <h3>health/db</h3>
            <p class="hint">GET /health/db</p>
            <div class="row">
              <button type="button" id="btn-health-db">実行</button>
            </div>
            <div class="output" id="out-health-db"></div>
          </section>
          <section class="panel">
            <h3>auth/login</h3>
            <p class="hint">POST /auth/login</p>
            <div class="field">
              <label for="login-username">username</label>
              <input id="login-username" type="text" autocomplete="username" />
            </div>
            <div class="field">
              <label for="login-password">password</label>
              <input id="login-password" type="password" autocomplete="current-password" />
            </div>
            <div class="field">
              <label for="login-expires">expires_in (seconds)</label>
              <input id="login-expires" type="number" min="60" step="60" value="3600" />
            </div>
            <div class="row">
              <button type="button" id="btn-login">実行</button>
            </div>
            <div class="output" id="out-login"></div>
          </section>
          <section class="panel">
            <h3>認証トークン</h3>
            <p class="hint">Authorization: Bearer &lt;token&gt;</p>
            <div class="field">
              <label for="token-input">token</label>
              <input id="token-input" type="text" placeholder="ログイン結果を貼り付け" />
            </div>
            <div class="row">
              <button type="button" class="secondary" id="btn-token-save">保存</button>
              <button type="button" class="secondary" id="btn-token-clear">削除</button>
            </div>
            <p class="hint" id="token-status">未設定</p>
          </section>
          <section class="panel">
            <h3>auth/me</h3>
            <p class="hint">GET /auth/me</p>
            <div class="row">
              <button type="button" id="btn-me">実行</button>
            </div>
            <div class="output" id="out-me"></div>
          </section>
          <section class="panel">
            <h3>signed-upload-url</h3>
            <p class="hint">POST /signed-upload-url</p>
            <div class="field">
              <label for="upload-key">key</label>
              <input id="upload-key" type="text" placeholder="uploads/2026-01-01/sample.txt" />
            </div>
            <div class="field">
              <label for="upload-content-type">content_type (optional)</label>
              <input id="upload-content-type" type="text" placeholder="text/plain" />
            </div>
            <div class="field">
              <label for="upload-expires">expires_in (seconds)</label>
              <input id="upload-expires" type="number" min="60" step="60" value="300" />
            </div>
            <div class="row">
              <button type="button" id="btn-upload-url">実行</button>
            </div>
            <div class="output" id="out-upload-url"></div>
          </section>
          <section class="panel">
            <h3>signed-download-url</h3>
            <p class="hint">GET /signed-download-url</p>
            <div class="field">
              <label for="download-key">key</label>
              <input id="download-key" type="text" placeholder="uploads/2026-01-01/sample.txt" />
            </div>
            <div class="field">
              <label for="download-expires">expires_in (seconds)</label>
              <input id="download-expires" type="number" min="60" step="60" value="300" />
            </div>
            <div class="row">
              <button type="button" id="btn-download-url">実行</button>
            </div>
            <div class="output" id="out-download-url"></div>
          </section>
        </div>
        <h2>補足</h2>
        <p><code>/auth/*</code> と署名URLは環境変数の設定が必要です。</p>
      </div>
    </main>
    <script>
      const tokenKey = "smoketestToken";
      let tokenValue = "";

      // 画面の出力欄へ結果を文字列で出すための共通処理です。
      function writeOutput(targetId, text) {
        const target = document.getElementById(targetId);
        if (target) {
          target.textContent = text;
        }
      }

      // 認証トークンの状態を画面に反映します。
      function refreshTokenStatus() {
        const status = document.getElementById("token-status");
        if (!status) {
          return;
        }
        status.textContent = tokenValue ? `設定済み (${tokenValue.length} 文字)` : "未設定";
      }

      // トークンの保存は再読込後も使えるよう sessionStorage に保存します。
      function setToken(nextToken) {
        tokenValue = (nextToken || "").trim();
        if (tokenValue) {
          sessionStorage.setItem(tokenKey, tokenValue);
        } else {
          sessionStorage.removeItem(tokenKey);
        }
        refreshTokenStatus();
      }

      // JSON API の疎通確認を行い、成否と内容を表示して結果も返します。
      async function callJsonApi(method, url, body, outId, needsAuth) {
        const headers = { "Content-Type": "application/json" };
        if (needsAuth) {
          // 認証必須のAPIはトークンが無いと意味のある結果にならないため先に案内します。
          if (!tokenValue) {
            writeOutput(outId, "token が未設定です。");
            return null;
          }
          headers.Authorization = `Bearer ${tokenValue}`;
        }
        try {
          const res = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
          });
          const text = await res.text();
          writeOutput(outId, `${res.status} ${res.statusText}\n${text}`);
          let data = null;
          // 応答が JSON の場合にだけ parse します。
          try {
            data = JSON.parse(text);
          } catch (_) {
            data = null;
          }
          return { res, text, data };
        } catch (err) {
          writeOutput(outId, `network error: ${err}`);
          return null;
        }
      }

      // 初期化時に保存済みトークンがあれば復元します。
      function initToken() {
        const saved = sessionStorage.getItem(tokenKey);
        if (saved) {
          tokenValue = saved;
        }
        refreshTokenStatus();
      }

      initToken();

      // UI 操作と API 呼び出しを結びつけます。
      document.getElementById("btn-health").addEventListener("click", () => {
        callJsonApi("GET", "/health", null, "out-health", false);
      });

      document.getElementById("btn-health-db").addEventListener("click", () => {
        callJsonApi("GET", "/health/db", null, "out-health-db", false);
      });

      document.getElementById("btn-login").addEventListener("click", async () => {
        const username = document.getElementById("login-username").value;
        const password = document.getElementById("login-password").value;
        const expires = Number(document.getElementById("login-expires").value) || 3600;
        const result = await callJsonApi(
          "POST",
          "/auth/login",
          { username, password, expires_in: expires },
          "out-login",
          false
        );
        // ログイン成功時の結果を読み取り、トークンを自動で保存します。
        if (result && result.data && result.data.token) {
          setToken(result.data.token);
          const tokenInput = document.getElementById("token-input");
          if (tokenInput) {
            tokenInput.value = result.data.token;
          }
        }
      });

      document.getElementById("btn-token-save").addEventListener("click", () => {
        const input = document.getElementById("token-input").value;
        setToken(input);
      });

      document.getElementById("btn-token-clear").addEventListener("click", () => {
        const input = document.getElementById("token-input");
        if (input) {
          input.value = "";
        }
        setToken("");
      });

      document.getElementById("btn-me").addEventListener("click", () => {
        callJsonApi("GET", "/auth/me", null, "out-me", true);
      });

      document.getElementById("btn-upload-url").addEventListener("click", () => {
        const key = document.getElementById("upload-key").value;
        const contentType = document.getElementById("upload-content-type").value || null;
        const expires = Number(document.getElementById("upload-expires").value) || 300;
        callJsonApi(
          "POST",
          "/signed-upload-url",
          { key, content_type: contentType, expires_in: expires },
          "out-upload-url",
          true
        );
      });

      document.getElementById("btn-download-url").addEventListener("click", () => {
        const key = encodeURIComponent(document.getElementById("download-key").value);
        const expires = Number(document.getElementById("download-expires").value) || 300;
        callJsonApi(
          "GET",
          `/signed-download-url?key=${key}&expires_in=${expires}`,
          null,
          "out-download-url",
          true
        );
      });
    </script>
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
