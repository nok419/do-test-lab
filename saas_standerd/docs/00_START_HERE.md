# START HERE（研究室 Web 公開基盤：DigitalOcean 標準化）

最終更新: 2026-02-03

このリポジトリは、研究室が **対外公開する実験用 Web アプリ** を、少人数の運用チームで安全に回すための「標準手順」と「テンプレ（スターターキット）」をまとめたものです。

---

## このドキュメントで“確立したい標準”
- **研究室ネットワーク/研究室PCを外部公開しない**
- アプリは **DigitalOcean App Platform** に載せる（OS運用を避ける）
- データ永続は **Managed PostgreSQL / Spaces** に寄せる（再デプロイ可能性）
- 監視・バックアップ・復旧を **最初に型化** する（実験中に詰まらない）
- 学生の開発はテンプレ/チェックリストに沿って **再現性** を持たせる

---

## まず最初に読む順番（おすすめ）
1. **`10_SCOPE.md`**: 何を解決する/しないか（前提の共有）
2. **`20_OPERATING_MODEL.md`**: 運用境界（誰が何を触るか）
3. **`60_SETUP_DIGITALOCEAN.md`**: DigitalOcean 側の「研究室共通基盤」を作る手順
4. **`50_SETUP_CLOUDFLARE.md`**:（使う場合）Cloudflare 側の標準化
5. **`80_SMOKETEST_STEP_BY_STEP.md`**: Smoke Test で土台を検証（最重要）
6. **`90_ONBOARD_NEW_APP.md`**: 学生アプリを標準の型で追加する

---

## リポジトリ構成（何がどこにあるか）
- `docs/`  
  この手順書一式（これが正）。
- `smoketest/fastapi-smoketest/`  
  最初にデプロイして土台を検証する Smoke Test アプリ（FastAPI）。
- `starter_kit/lab_platform_starter_kit/`  
  学生が新規アプリを作るためのテンプレ・AppSpec例・チェックリスト・バックアップスクリプト。
- `tools/`  
  シークレット生成・ユーザ生成など、運用で使う小ツール。

---

## 本書の用語
- **Platform運用チーム（Platform Ops）**: 研究室の少人数の運用担当。Cloudflare/DigitalOcean の権限とコスト責任を持つ。
- **App Owner（アプリ担当）**: 学生（または研究員）。アプリ実装とアプリ内のデータ保護責任を持つ。
- **参加者（Participant）**: 外部の実験参加者。アプリ内での権限は最小にする（通常は閲覧不可）。

---

## まずの到達点（“標準化できた”判定）
次の条件を満たすと「標準化環境の土台ができた」と判断します：

- Smoke Test が App Platform にデプロイされている  
  - `/health` が 200
  - `/health/db` が 200（DB疎通）
  - Spaces への署名付きURLでアップロードできる
- **日次バックアップ**（`pg_dump -> Spaces`）が動き、ログで成功確認できる
- **復旧手順を1回通した**（別DBへ restore して動作確認）
- 監視（最低限）が入っている  
  - App Platform Alerts（デプロイ失敗/ドメイン失敗）
  - Uptime（`/health` の外形監視）

上記の実現手順は `80_SMOKETEST_STEP_BY_STEP.md` に集約しています。

---

## 旧版ドキュメント
過去の作業メモ/旧版手順は `docs/archive/` に退避しています（参照用、現行運用の正ではありません）。
