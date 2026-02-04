# Smoke Test 手順（基盤を“先に”検証する）

最終更新: 2026-02-03

この手順は「学生アプリを載せる前に、土台（運用）が耐えるか」を検証するためのものです。  
最初の1本は機能より **運用の健全性** を優先します。

対象アプリ：`smoketest/fastapi-smoketest/`

---

## 0. 事前条件（ここが揃っていないと先に進まない）
- DigitalOcean Team が作成済み（Team Contact Email / Billing alert 済み）
- Managed PostgreSQL が作成済み
- Spaces バケットが作成済み（例: `lab-prod-backups`, `lab-prod-uploads`）
- GitHub リポジトリが作れる

---

## 1. Smoke Test アプリを GitHub へ push
1. `smoketest/fastapi-smoketest/` を新規リポジトリへ
2. `main` ブランチで push

推奨：
- production 運用なら main 保護 + PR運用（最低限レビュー）

---

## 2. Smoke Test 用の DB を作る（1アプリ=1DBユーザ）
Managed PostgreSQL で次を作成します（Platform Ops 作業）：

- DB名（例）: `db_smoketest`
- ユーザ（例）: `u_smoketest`
- パスワードは安全に生成し、接続文字列を控える

接続情報：
- `DATABASE_URL`（例: `postgres://...`）
- SSL/TLS が必要な場合は接続文字列に反映

---

## 3. Smoke Test 用の Spaces キーを発行（Per-bucket 推奨）
- バケット（例）:
  - アップロード: `lab-prod-uploads`
  - バックアップ: `lab-prod-backups`
- 権限:
  - アップロード: read/write（必要最小）
  - バックアップ: write（必要最小）

控えるもの：
- `SPACES_ACCESS_KEY_ID`
- `SPACES_SECRET_ACCESS_KEY`
- `SPACES_ENDPOINT_URL`（例: `https://sgp1.digitaloceanspaces.com`）
- `SPACES_REGION`（例: `sgp1`）

---

## 4. Secrets を生成（ローカルで生成して貼り付け）
このリポジトリのツールを使います。

### 4.1 AUTH_TOKEN_SECRET
```bash
python tools/gen_secret.py --bytes 32 --format urlsafe
```

### 4.2 AUTH_USERS_JSON（管理者ユーザ）
例：`admin` を作る（roleは `admin`）
```bash
python tools/gen_user.py --username admin --role admin
```

出力された JSON オブジェクトを `[` と `]` で囲んで配列にして、`AUTH_USERS_JSON` に入れます。

---

## 5. App Platform でアプリを作成（Web Service）
1. DigitalOcean → App Platform → Create App
2. GitHub を選択し、リポジトリと `main` を選ぶ
3. Component:
   - Web Service（Dockerfile）
   - HTTP port: `8080`
4. Region: DB/Spaces と揃える（例: SGP）
5. サイズ:
   - まずは最小/固定（費用と挙動の固定が目的）

### 5.1 環境変数（Runtime）を設定（Encrypt推奨）
必須：
- `PORT=8080`
- `DATABASE_URL`（Encrypt）
- Spaces
  - `SPACES_BUCKET`（例: `lab-prod-uploads`）
  - `SPACES_REGION`
  - `SPACES_ENDPOINT_URL`
  - `SPACES_ACCESS_KEY_ID`（Encrypt）
  - `SPACES_SECRET_ACCESS_KEY`（Encrypt）
- Auth
  - `AUTH_TOKEN_SECRET`（Encrypt）
  - `AUTH_USERS_JSON`（Encrypt）

---

## 6. 動作確認（最低限の合格条件）
デプロイ後、以下を確認します。

### 6.1 /health
- `GET https://<app-default-domain>/health` → 200

### 6.2 /health/db
- `GET https://<app-default-domain>/health/db` → 200  
  ※ 503 の場合は DB 接続設定を疑う

### 6.3 認証（ログイン→トークン）
- `POST /auth/login` で token が返る
- `GET /auth/me` が 200

---

## 7. Spaces（署名付きURL）確認
1. `POST /signed-upload-url` で PUT 用 URL を発行
2. そのURLへファイルを PUT できる
3. （研究者ロールで）`GET /signed-download-url` で GET URL を発行し、ダウンロードできる

> 参加者にダウンロード権限を与えるかは設計次第です。  
> 標準テンプレでは “研究者のみダウンロード可” に寄せています。

---

## 8. 日次バックアップ Job を設定（必須：production）
Smoke Test でも必ず回して、運用の土台を作ります。

### 8.1 Job の作り方（App Platform）
- Job type: Scheduled
- Cron: `0 3 * * *`（例）
- Time zone: `Asia/Tokyo`
- Image: `Dockerfile.backup`
- Run command: `bash scripts/backup_pg_to_spaces.sh`

### 8.2 Job 環境変数
必須：
- `APP_NAME=smoketest`
- `DATABASE_URL`（Encrypt）
- `SPACES_BUCKET`（例: `lab-prod-backups`）
- `SPACES_ENDPOINT_URL`
- `SPACES_BACKUP_PREFIX=backups`
- AWS credentials（Encrypt）
  - `AWS_ACCESS_KEY_ID`（Spacesのキー）
  - `AWS_SECRET_ACCESS_KEY`（Spacesのキー）

※ スクリプトは `SPACES_ACCESS_KEY_ID` / `SPACES_SECRET_ACCESS_KEY` が入っている場合、AWS_* に自動で寄せるようにしています（テンプレ側で対応）。

### 8.3 成功確認
- Job のログに `done: s3://...` が出る
- Spaces に dump が作成される

---

## 9. 復旧訓練（必須：本番前に1回）
**原則：別DBに復旧して切り替え** を推奨します（破壊的復旧を避ける）。

1. 復旧先の新しい DB（例: `db_smoketest_restore`）を作る
2. `DUMP_OBJECT_KEY` を指定して restore を実行  
   - `scripts/restore_pg_from_dump.sh`
3. アプリの `DATABASE_URL` を復旧先に差し替えて起動確認
4. 問題なければ元に戻す（または切り替え）

---

## 10. ここまでの合格基準（Gate）
- [ ] /health が安定して 200（外形監視が成立する）
- [ ] DB 疎通が取れている（/health/db）
- [ ] Spaces 署名付きURLでアップ/ダウンロードできる
- [ ] 日次バックアップ Job が成功する
- [ ] restore 手順を1回通した（別DBでOK）

合格したら：
- `90_ONBOARD_NEW_APP.md` に進んで、学生アプリの運用に移ります。
