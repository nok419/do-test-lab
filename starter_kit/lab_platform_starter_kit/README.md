# lab_platform_starter_kit

研究室Webサービス運営基盤（DigitalOcean標準 + Cloudflare前段）のためのスターターキットです。

このキットでやること
- Node / Python の最小テンプレを用意し、App Platformにそのまま載せられる形にします
- Spaces（S3互換）を前提に、ファイル転送は「署名付きURL」で行う前提の雛形を入れます
- 認証とRBACの最小実装（環境変数でユーザ定義する方式）を同梱し、参加者データを保護する前提を作ります
- App Platform Jobで日次バックアップ（pg_dump -> Spaces）を回す雛形を入れます
- 再デプロイ可能性を担保するため、AppSpec（YAML）の例/雛形を同梱します
- Cloudflare前段（DNS/Proxy/WAF/Rate Limit）のチェックリストを同梱します

詳細な方針・導入手順・運用ルールは、本リポジトリの `docs/`（特に `docs/00_START_HERE.md`）を参照してください。

## ディレクトリ構成

- templates/
  - python-fastapi/
  - node-express-ws/
- app_spec_examples/
  - app_fastapi.yaml
  - app_node_ws.yaml
  - app_template_base.yaml
- docs/
  - cloudflare_edge_checklist.md
  - go_live_checklist.md
- scripts/
  - backup_pg_to_spaces.sh
  - restore_pg_from_dump.sh
- labctl/
  - labctl.py（テンプレ生成用の簡易CLI）

## まず最初にやること（最小手順）

1. templates から近いものを選んで、新規リポジトリを作成します
2. app_spec_examples のYAMLをコピーし、リポジトリ名と必要な環境変数名を調整します（迷ったら `app_template_base.yaml` から）
3. DigitalOcean App Platformでアプリを作成し、環境変数（Encrypt）を設定します
   - 認証（RBAC）のために、AUTH_TOKEN_SECRET と AUTH_USERS_JSON を設定します
   - templates/*/scripts/gen_auth_user.* でユーザ定義（salt/hash）を生成できます
4. Spacesバケットを作成し、Limited access keyを発行します（バケット単位）
5. Managed PostgreSQLにDBとUserを作成し、DATABASE_URLを発行します
6. Job（バックアップ）を追加し、日次でpg_dumpをSpacesへ退避します
7. 公開前に `docs/cloudflare_edge_checklist.md` の手順でCloudflare前段を整備します

## 注意

- SpacesのLimited access keyは、現時点ではControl Panelで発行する前提です（自動化しにくい箇所です）
- バックアップと復旧は「一度は手で通す」ことを必須にしてください（実験最終日に詰みやすいので）
