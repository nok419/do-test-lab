# Changelog

## 2026-02-03
- ドキュメント構成を全面的に整理し、現行手順書を `docs/` に再編
  - 旧版は `docs/archive/` に退避（参照用）
- 運用境界（役割/権限/責任分界）を詳細化（`docs/20_OPERATING_MODEL.md`）
- DigitalOcean 導入〜標準化環境確立までの手順を “Smoke Test 起点” で再設計
  - `docs/60_SETUP_DIGITALOCEAN.md`
  - `docs/80_SMOKETEST_STEP_BY_STEP.md`
  - `docs/90_ONBOARD_NEW_APP.md`
- 運用テンプレ追加（申請/台帳/インシデント/変更申請）: `ops/templates/`
- バックアップ運用を改善
  - backup/restore スクリプトで `SPACES_*` と `AWS_*` の取り回しを整理
  - 世代削除（retention）用 `prune_pg_backups.sh` を追加
  - `Dockerfile.backup` に coreutils(date) を追加
- `tools/gen_user.py` のロール選択をテンプレに合わせて修正（admin/researcher/assistant/participant）

## 2026-02-01
- 初期バンドル生成（旧版ドキュメントを含む）
