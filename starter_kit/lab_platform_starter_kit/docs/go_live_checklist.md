# Go-Live Checklist (production)

最終更新: 2026-02-03

目的：
- 「実験中に落ちる/戻せない」を避けるための最低限のチェックを揃える
- 研究室の運営チームが“土壌”として担保すべき範囲を明確にする

---

## 1. 入口（Cloudflareを使う場合のみ）
### 1.1 Cloudflare = DNS only の場合
- 参加者導線のHTTPSが有効（App Platform 側のSSL Active を確認）
- DNSレコード（CNAME）が正しい

### 1.2 Cloudflare = Proxy（オレンジ雲）の場合
- 対象サブドメインが Cloudflare Proxy 配下
- HTTPS強制（例：Always Use HTTPS）
- Rate Limit（最低限：ログイン、署名付きURL発行系、WebSocket接続など）
- 必要ならTurnstile等（参加者導線に影響が出るため段階導入）
- “ドメイン検証/証明書更新” を阻害しない運用になっている（詰まったら DNS only に戻して切り分け）

---

## 2. DigitalOcean App Platform（実行）
- `instance_count` が明示されている（コストと挙動を固定する）
- `/health` が200を返し、health check / liveness が設定されている
- 環境変数（特にSECRET）がコンソール以外に漏れていない（Gitに入っていない）
- ログがDO側で追える（stdout/stderr）

---

## 3. Managed PostgreSQL（DB）
- DB/Userがプロジェクト単位で分離されている（最低限）
- 自動バックアップが有効
- Trusted Sources の運用が決まっている（アプリ以外の接続制御）
- 可能なら実験前に「リストア手順を1回通す」（本番で初めてやらない）

---

## 4. Spaces（ファイル）
- バケットが Private で運用されている
- バージョニングが有効（可能なら）
- バケット単位で access key を発行している（最小権限）
- 参加者がブラウザから PUT する場合は CORS を必要最小で設定

---

## 5. バックアップ（Job）
- 日次バックアップJob（`pg_dump -> Spaces`）が動き、成功ログが確認できる
- 失敗時の通知/確認導線がある（Alerts/運用担当の定期確認など）
- （推奨）世代削除（retention）の方針がある
  - 手動でも可 / 自動化するなら `prune_pg_backups.sh`

---

## 6. アプリ側（“土壌”として要求する最低限）
- 認証 + RBAC（参加者がデータ閲覧できない等）が効いている
- 大容量ファイルは署名付きURL等でSpaces直（アプリ帯域を食い潰さない）
- 個人情報をログに出さない（メール等を収集する場合は特に注意）
