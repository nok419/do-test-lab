# 標準スタック定義（“この型に乗せる”の中身）

最終更新: 2026-02-03

この章は「学生アプリを載せるときに毎回同じ形になる」ための規約です。

---

## 1. アプリ共通インタフェース（必須）
全アプリで必ず実装する（テンプレ準拠）：

- `GET /health`  
  - 200 と `{ "ok": true }` を返すだけ  
  - 外形監視と liveness の基点
- `GET /health/db`（推奨）  
  - DB疎通確認（障害切り分けに有効）
- ログは stdout/stderr に出す  
  - 重要：個人情報（PII）をログに出さない
- 設定は環境変数  
  - Secrets は App Platform の Encrypt を使用

---

## 2. 永続化の原則（必須）
- アプリのローカルディスクに永続データを置かない  
  → App Platform のコンテナは入れ替わる前提
- 永続先は次のどちらか：
  - DB（研究データ、メタデータ）
  - Spaces（ファイル、バックアップ、成果物）

---

## 3. 標準コンポーネント（推奨）
### 3.1 App Platform
- instance_count: 1（コストと挙動を固定）
- instance_size_slug: 最小〜中（アプリ要件で決める）
- alerts: DEPLOYMENT_FAILED / DOMAIN_FAILED
- health_check/liveness_health_check: `/health`

### 3.2 Managed PostgreSQL
- 1アプリ = 1DBユーザ
- Trusted Sources: app のみ許可
- 自動バックアップは有効
- 重要: production 前に復旧訓練（別DBにrestore）

### 3.3 Spaces
- バケットは Private
- Versioning を有効化（可能なら）
- Per-bucket access key を使う
- ブラウザ直PUTが必要なときだけ CORS を設定

---

## 4. 標準の環境変数（テンプレの前提）
### 4.1 必須
- `PORT`（例: `8080`）
- `DATABASE_URL`（Secret）
- Spaces
  - `SPACES_BUCKET`
  - `SPACES_REGION`
  - `SPACES_ENDPOINT_URL`
  - `SPACES_ACCESS_KEY_ID`（Secret）
  - `SPACES_SECRET_ACCESS_KEY`（Secret）
- 認証（RBAC）
  - `AUTH_TOKEN_SECRET`（Secret）
  - `AUTH_USERS_JSON`（Secret）

### 4.2 推奨（運用を楽にする）
- `APP_NAME`（例: `exp-xxx`）
- `APP_ENV`（`test` / `production` / `archive`）
- バックアップ
  - `SPACES_BACKUP_PREFIX`（例: `backups`）
  - `BACKUP_RETENTION_DAYS`（例: `30`）

---

## 5. バックアップの標準（必須：production）
- Managed DB の自動バックアップ（基盤）
- 追加で「論理バックアップ（pg_dump）」を日次で Spaces に退避  
  - スクリプト: `scripts/backup_pg_to_spaces.sh`
  - 実行: App Platform Scheduled Job

さらに推奨：
- 世代保持を運用で担保（削除/整理）
  - `scripts/prune_pg_backups.sh` を追加ジョブで回す（後述）

---

## 6. 監視の標準（最低限）
- App Platform Alerts（デプロイ失敗/ドメイン失敗）
- Uptime（`/health` 外形監視）
- （推奨）バックアップジョブの成功ログ確認（週1でも良い）

---

## 7. 標準のテンプレ/チェックリスト
- テンプレ:
  - `starter_kit/lab_platform_starter_kit/templates/python-fastapi/`
  - `starter_kit/lab_platform_starter_kit/templates/node-express-ws/`
- AppSpec例:
  - `starter_kit/lab_platform_starter_kit/app_spec_examples/`
- Go-Live Checklist:
  - `starter_kit/lab_platform_starter_kit/docs/go_live_checklist.md`

---

## 8. 認証・RBACの標準ロール
テンプレの標準ロールは以下です（統一）：
- `admin`
- `researcher`
- `assistant`
- `participant`

※ 参加者（participant）にログインを与えない設計もあり得ます。  
その場合でも「参加者が研究データを閲覧できない」ことが最優先です。

ロール運用の詳細は `120_SECURITY_BASELINE.md` を参照してください。
