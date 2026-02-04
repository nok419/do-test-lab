# 新規アプリ追加手順（学生アプリを標準の型で増やす）

最終更新: 2026-02-03

この章は、Smoke Test 合格後に「実験アプリを増やす」ための標準手順です。  
運用境界（OpsがDOを触る/学生はGitHubまで）を前提に記載します。

---

## 0. 前提
- Smoke Test が合格済み（`80_SMOKETEST_STEP_BY_STEP.md`）
- 命名規則（サブドメイン/アプリ名）が決まっている
- App Owner（学生）と Platform Ops が決まっている

---

## 1. App Owner がやること（GitHub側）
### 1.1 テンプレからプロジェクト作成
選択肢：
- Python: `starter_kit/lab_platform_starter_kit/templates/python-fastapi/`
- Node: `starter_kit/lab_platform_starter_kit/templates/node-express-ws/`

手動でコピーしても良いですが、`labctl` を使うと事故が減ります。

例（Python）:
```bash
python starter_kit/lab_platform_starter_kit/labctl/labctl.py new --template python-fastapi --output ./exp-xxx
```

### 1.2 リポジトリ作成 → push
- 新規リポジトリ `exp-xxx` を作り、push
- `.env` はコミットしない（Secrets禁止）

---

## 2. App Owner が書く “申請”（Opsに渡す）
`ops/templates/experiment_request.md` を埋めて提出します。

最低限必要な情報：
- アプリ名（slug）
- 予定サブドメイン（`exp-xxx.lab...`）
- DBの要否（必要ならスキーマ概略）
- Spaces の用途（アップロード/成果物/バックアップ）
- データ保持期間（例: 90日）
- 公開範囲（参加者/研究室内）

---

## 3. Platform Ops がやること（DigitalOcean側）
### 3.1 DB の払い出し（1アプリ=1DBユーザ）
- DB: `db_exp_xxx`
- User: `u_exp_xxx`
- `DATABASE_URL` を作成して控える

### 3.2 Spaces の払い出し（最小権限）
用途に応じてバケット/キーを決めます。

例：
- 参加者アップロード → `lab-prod-uploads` の prefix を分ける  
  もしくはバケットを分ける（件数が増えるなら分けた方が安全）
- バックアップ → `lab-prod-backups` に集約（prefixは app ごと）

Per-bucket access key を基本にする。

### 3.3 App Platform アプリ作成
方法は2通り：

- **UIで作る（簡単）**  
  GitHub連携で作成 → 環境変数をセット
- **AppSpecで作る（再現性が高い）**  
  `starter_kit/lab_platform_starter_kit/app_spec_examples/app_template_base.yaml` をコピーして編集し、適用する

どちらでも良いが、production は AppSpec 管理（台帳+再現性）を推奨。

### 3.4 バックアップ Job を作る（production は必須）
- Smoke Test と同様に Scheduled Job を設定
- 成功ログを確認

---

## 4. Domain を割り当てる
- DigitalOcean 側で custom domain を追加
- DNS（Cloudflare等）に CNAME を追加（最初は DNS only 推奨）
- `https://exp-xxx.../health` が 200 を確認

Cloudflare Proxy を使う場合は `50_SETUP_CLOUDFLARE.md` の注意に従う。

---

## 5. Go-Live（production）チェック
- `starter_kit/lab_platform_starter_kit/docs/go_live_checklist.md` を必ず通す
- 特に重要：
  - Secrets の取り扱い
  - バックアップが回っていること
  - restore を1回通していること（可能なら）

---

## 6. 実験中の運用（変更凍結）
- production 中は原則変更を抑える（緊急のみ）
- 緊急修正の前にバックアップ状況を確認する
- 週1で台帳と稼働状況を棚卸し（`130_COST_GUARDRAILS.md`）

---

## 7. 実験終了（archive）
- `150_OFFBOARDING.md` の手順で停止/アーカイブ/削除を実施
- 台帳更新が完了条件
