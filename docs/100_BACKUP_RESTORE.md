# バックアップ/復旧（Runbook）

最終更新: 2026-02-03

この章は「データが消えた」「戻せない」を避けるための手順書です。  
production では **“バックアップがある” ではなく “戻せる”** を必須にします。

---

## 1. 標準方針（2段構え）
### 1.1 Managed DB の自動バックアップ（基盤）
- DigitalOcean の Managed PostgreSQL による自動バックアップ
- 利点：運用が軽い、復旧導線が用意されている
- 注意：細かい保持/持ち出しには向かない場合がある

### 1.2 論理バックアップ（pg_dump → Spaces）（標準で追加）
- App Platform Scheduled Job で日次実行
- 利点：Spacesに退避でき、アーカイブ/持ち出しが容易
- 注意：復旧には手順と検証が必要

---

## 2. RPO/RTO の最低ライン（目安）
研究室運用の最小目標（例）：
- RPO（失ってよいデータ量）: 24h
- RTO（復旧に許容する時間）: 数時間以内（当日中）

プロジェクトによって変える場合は申請（`ops/templates/experiment_request.md`）に明記します。

---

## 3. 日次バックアップ Job（標準）
### 3.1 スクリプト
- `scripts/backup_pg_to_spaces.sh`

### 3.2 実行環境
- App Platform の Scheduled Job
- `Dockerfile.backup` を使用（pg_dump + aws cli）

### 3.3 成功判定
- Jobログに `done: s3://...` が出る
- Spaces に dump ファイルが作られている

---

## 4. 世代保持（Retention）
最低限の方針：
- production: 30日保持（例）
- 実験終了後: 90日保持（例）→ その後削除可否を判断

実装方法：
- 手動でも良い（台帳に “最終削除日” を残す）
- 自動化したい場合は `scripts/prune_pg_backups.sh` を Scheduled Job で回す

---

## 5. 復旧手順（推奨：別DBに復元して切り替え）
### 5.1 原則（破壊的復旧を避ける）
- 既存DBに `--clean` で上書き復旧は事故リスクが高い  
  → 新しいDBに restore して、切り替える

### 5.2 手順（別DB restore）
1. 復旧先の DB を作成（例: `db_exp_xxx_restore_20260203`）
2. `DUMP_OBJECT_KEY` を指定して restore を実行  
   - `scripts/restore_pg_from_dump.sh`
3. アプリの `DATABASE_URL` を復旧先に切り替え
4. `/health/db` で疎通確認
5. アプリ機能（最低限）を確認
6. 問題なければ、復旧先を正として運用継続

### 5.3 破壊的復旧（最終手段）
- `scripts/restore_pg_from_dump.sh` は `--clean` を使います
- production でやる前に Platform Owner と合意し、必ず記録を残す

---

## 6. 復旧訓練（production 前に必須）
- Smoke Test 時点で1回
- 各 production アプリも go-live 前に可能なら1回（最小でも smoke test で担保）

---

## 7. 典型トラブルと対処
- restore が失敗する：
  - ダンプ形式が違う（custom formatか）
  - DB接続先が間違っている
  - 権限/SSL設定
- dump が大きすぎる：
  - DB肥大化、不要データ削除、圧縮、リテンション見直し

障害対応の全体は `140_RUNBOOKS.md` にまとめています。
