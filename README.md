# 研究室・実験Webアプリ公開基盤（標準化パッケージ）: DigitalOcean（App Platform）中心

最終更新: 2026-02-03

研究室が **対外公開する実験用Webアプリ** を、少人数の運用チームで安全に回すための
「標準手順（docs）」と「テンプレ（starter_kit）」と「Smoke Test」をまとめたリポジトリです。

---

## まずやること（おすすめの順番）
1. `docs/00_START_HERE.md` を読む（全体像）
2. `docs/60_SETUP_DIGITALOCEAN.md` を実施（研究室共通の土台を作る）
3. `docs/80_SMOKETEST_STEP_BY_STEP.md` を実施（運用の健全性を検証）
4. `docs/90_ONBOARD_NEW_APP.md` で学生アプリを追加

---

## 想定アーキテクチャ（標準）
- Compute: DigitalOcean App Platform
- DB: DigitalOcean Managed PostgreSQL
- Object Storage: DigitalOcean Spaces（S3互換）
- Monitoring: App Platform Alerts + Uptime（外形監視）
- Edge（任意）: Cloudflare（DNS/Proxy/WAF/Rate Limit）

---

## ディレクトリ
- `docs/` … 標準手順書（現行の正）
- `smoketest/` … 基盤を先に検証する Smoke Test アプリ
- `starter_kit/` … 学生向けテンプレ（AppSpec例 / バックアップスクリプト / チェックリスト）
- `tools/` … 運用補助（secrets生成・ユーザ生成）
- `ops/` … 申請/台帳/インシデント等のテンプレ

---

## この基盤で守ること（最重要）
- 研究室PC/ネットワークを直に外部公開しない
- Secrets を Git や共有ドキュメントに置かない（App Platform Encryptへ）
- “バックアップがある” ではなく “戻せる” を go-live 前に確認する
- 実験終了後は archive/cleanup までやり切り、不要課金を止める

