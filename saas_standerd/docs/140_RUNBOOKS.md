# 障害対応 Runbook（よくある事故の手順）

最終更新: 2026-02-03

この章は「困ったらここを見る」ための実務手順です。  
原則：**データ保護 > 復旧 > 原因究明** の順で動きます。

---

## 0. 共通（最初の5分でやること）
- [ ] 影響範囲を確認（参加者導線？管理画面だけ？全停止？）
- [ ] 直近の変更を確認（デプロイ、環境変数、DNS）
- [ ] まず `/health` を確認（外形監視と同じ観点）
- [ ] Platform Ops と App Owner の両方に共有（属人化を防ぐ）

---

## 1. 症状：/health が 5xx / タイムアウト
### 1.1 まず確認
- App Platform の “Deployments” に失敗が出ていないか
- ログ（stdout/stderr）に例外が出ていないか
- リソース不足（メモリ不足で落ちていないか）

### 1.2 対処（優先順）
1. 直近デプロイが原因なら **ロールバック**（可能なら）
2. 直近の環境変数変更が原因なら差し戻し
3. 短期回避として instance size を一段上げる（コスト注意）
4. 根本原因は App Owner が修正 → デプロイ

---

## 2. 症状：/health は 200 だが /health/db が 503
### 2.1 原因候補
- `DATABASE_URL` が間違っている
- DB 側のメンテ/停止
- Trusted Sources でブロックされている
- 接続数上限（アプリがコネクション張りすぎ）

### 2.2 対処
1. DB の稼働状態（DigitalOcean DB画面）を確認
2. `DATABASE_URL` を再確認（host/db/user/sslmode）
3. Trusted Sources の設定を確認（App を許可できているか）
4. 一時回避：
   - 影響が大きければ “調査用に復元したDB” に切り替える
   - もしくは接続設定/プール設定を見直す（App Owner）

---

## 3. 症状：ドメイン/TLS エラー（404, 525/526, 530, etc）
### 3.1 まず確認
- DigitalOcean 側で Domain status が Verified / SSL Active か
- DNS の CNAME が正しいか
- Cloudflare Proxy を使っているか（DNS onlyか）

### 3.2 よくある対処
- Domain verification で詰まる：
  - Cloudflare を DNS only に戻す → 検証 → SSL Active を確認
- SSL/TLS エラー（CloudflareをProxyしている場合）：
  - Origin（DO）が正しい証明書を返しているか（SSL Active）
  - Cloudflare SSL mode が Full (strict) になっているか（要件次第）
- 切り分けの基本：
  - **DNS only に戻して直るなら入口（Cloudflare）側の問題**

---

## 4. 症状：Spaces が 403 / 署名付きURLが効かない
### 4.1 まず確認
- `SPACES_ENDPOINT_URL` / `SPACES_REGION` が正しいか
- `SPACES_BUCKET` が正しいか
- Access key が正しいか（per-bucket なら対象バケットに紐づいているか）
- 署名URLの有効期限が短すぎないか

### 4.2 対処
1. アプリの環境変数を再確認
2. Spaces 側でキーを再発行 → 旧キーを無効化
3. CORS が必要なケースなら、バケットにCORSを設定

---

## 5. 症状：バックアップ Job が失敗
### 5.1 まず確認
- Job ログで失敗箇所（pg_dump? upload?）
- `DATABASE_URL` / Spaces credentials の設定
- Spaces バケットが存在するか

### 5.2 対処
1. 設定ミスなら修正して再実行
2. どうしても復旧が必要なら：
   - ローカル環境で `pg_dump` を実行 → Spacesへ手動アップロード
   - ただし credentials の取り扱いに注意（漏えい禁止）

---

## 6. 症状：コストが急増（Billing alert が鳴った）
1. “稼働中アプリ” を台帳で確認
2. 不要アプリを archive（アプリ停止 + job停止）
3. DB の縮退/停止（方針に従う）
4. Spaces のバックアップ世代/不要データを整理
5. Platform Owner に報告（原因と対策）

---

## 7. 症状：漏えい疑い / 不正アクセス疑い（最優先）
**最初にやること：被害拡大を止める**
1. 該当アプリを一時停止（または入口で遮断）
2. Secrets をローテーション
   - AUTH_TOKEN_SECRET
   - AUTH_USERS_JSON（全ユーザ）
   - Spaces keys
   - DB パスワード（必要なら）
3. 影響範囲の確認（ログ/アクセス履歴）
4. Platform Owner へ即時連絡（外部連絡が必要な場合がある）
5. 再開判断は Platform Owner と合意して実施

---

## 8. 記録（必須）
障害が落ち着いたら、以下を残します：
- いつ、何が、誰に影響したか
- 暫定対応と恒久対応
- 再発防止（チェックリスト/テンプレの修正）

テンプレは `ops/templates/incident_report.md` を利用してください。
