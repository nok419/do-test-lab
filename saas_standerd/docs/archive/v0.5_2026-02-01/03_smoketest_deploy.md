# Smoke Test アプリをデプロイして基盤を検証する

この手順は「学生アプリを乗せる前に、運用の地盤を固める」ためのものです。  
対象アプリ：`smoketest/fastapi-smoketest/`

---

## 0) 事前に用意するもの
- GitHubアカウント（研究室のOrgでも個人でも可）
- DigitalOceanアカウント（研究室Teamに招待）
- Cloudflare（ドメインゾーンが設定済み）

---

## 1) Smoke Test アプリをGitHubへpush
1. `smoketest/fastapi-smoketest/` を作業ディレクトリにコピー
2. GitHubで新しいリポジトリを作成
3. commit & push

（テンプレは `Dockerfile` でビルドできるので、App Platform側は迷いにくいです）

---

## 2) DigitalOcean App Platformでアプリ作成
1. Create App → GitHub を選ぶ
2. リポジトリとブランチ（main）を選択
3. Component は Web Service（Dockerfile）を選ぶ
4. リージョンを選択（例：SGP）
5. サイズ（最初は最小で固定推奨）
   - `apps-s-1vcpu-0.5gb`（$5/月）
   - 余裕を見たいなら `apps-s-1vcpu-1gb-fixed`（$10/月）

---

## 3) 環境変数（Secrets含む）を設定
App Platform の Environment Variables に設定します（必要なものは Encrypt）。

### 必須
- `AUTH_TOKEN_SECRET`  
  - `python tools/gen_secret.py --bytes 32 --format urlsafe`
- `AUTH_USERS_JSON`  
  - 例：管理者ユーザを作る
    - `python tools/gen_user.py --username admin --role admin`
    - 出力されたJSONを `[` と `]` で囲って貼り付け

### DB（後で繋ぐ場合）
- `DATABASE_URL`  
  - Managed PostgreSQL の接続文字列

### Spaces（後で繋ぐ場合）
- `SPACES_BUCKET`
- `SPACES_REGION`
- `SPACES_ENDPOINT_URL`（例: `https://sgp1.digitaloceanspaces.com`）
- `SPACES_ACCESS_KEY_ID`
- `SPACES_SECRET_ACCESS_KEY`

---

## 4) デプロイ後の確認（最低限）
- `https://<app-domain>/health` → `{"ok": true}`
- `POST /auth/login` でトークンが出る
- `GET /health/db`（DBを繋いだら）で 200 が返る

---

## 5) Cloudflareに載せる（サブドメイン割当）
1. Cloudflare DNSで `exp-smoke` などの CNAME を作成し、`<app>.ondigitalocean.app` を指す
2. ProxyをON
3. HTTPS強制（Always Use HTTPS）を確認

---

## 6) Uptime監視を入れる
- `/health` を監視対象にする
- 落ちたら通知（Email）

---

## 7) バックアップの疎通（任意だが推奨）
- `starter_kit/scripts/backup_pg_to_spaces.sh` を App Platform Job として定期実行
- いちど復旧手順（restore）を通す  
  → 「戻せる」が確認できてはじめて実験運用に入る

