# セキュリティ基準（最低限の“型”）

最終更新: 2026-02-03

研究室運用で事故が起きやすいのは「人の入れ替わり」「属人化」「Secretsの漏えい」です。  
この章は **最低限の共通ルール** をまとめます。

---

## 1. アカウント/権限（必須）
### 1.1 DigitalOcean
- 2FA 必須
- Owner 権限は最小人数に限定
- Team Contact Email を共同メアドにする（通知が消えないように）

### 1.2 Cloudflare（使う場合）
- Admin 権限は Platform Ops に限定
- DNS変更権限が誰にあるかを明確化

---

## 2. Secrets 管理（必須）
### 2.1 禁止事項
- Secrets を Git に入れる（`.env` も含む）
- Secrets を Wiki/スプレッドシートに平文で貼る
- Slack等に平文で貼る

### 2.2 標準の置き場所
- **DigitalOcean App Platform の環境変数（Encrypt）**  
  - `DATABASE_URL`
  - `AUTH_TOKEN_SECRET`
  - `AUTH_USERS_JSON`
  - Spaces keys など

補助：
- Secrets の“控え”はパスワードマネージャ等に置く（運用チームのみ）

### 2.3 ローテーション
- 学生卒業/離脱、漏えい疑い、実験終了時にローテーション（または無効化）
- Spaces のキーは per-bucket を前提に、影響範囲を限定する

---

## 3. 認証・RBAC（必須）
### 3.1 標準ロール
テンプレの標準ロール（統一）：
- `admin`: 運用・全権
- `researcher`: 研究データ閲覧/管理
- `assistant`: 補助（必要なら）
- `participant`: 参加者（基本は閲覧不可に寄せる）

### 3.2 基本ルール
- 参加者が研究データ（他者の回答含む）を閲覧できない
- 管理系 API は必ず role を絞る
- 認証情報は短寿命トークン（テンプレは exp 付き）を前提

---

## 4. DB セキュリティ（必須）
- 1アプリ=1DBユーザ（他アプリへの横展開を防ぐ）
- Trusted Sources を有効にしてアプリ以外の接続を絞る
- ローカル接続が必要なら一時的に許可し、期限を決めて削除

---

## 5. Spaces セキュリティ（必須）
- 原則 Private
- 署名付きURLで必要な操作だけ許可
- per-bucket access key を使う
- 参加者が直接 PUT する場合の注意
  - キーを参加者に渡さない（署名付きURLのみ）
  - prefix を分けて混線を避ける

---

## 6. ログ/個人情報（必須）
- PII（メール、氏名、住所、自由記述の生データ等）をログに出さない
- エラー時も「入力値の全文」を吐かない（必要ならマスク）

---

## 7. 入口防御（任意）
- Cloudflare Proxy を使う場合は WAF/Rate Limit を段階導入
- Cloudflare Access 等で管理画面を守りたい場合：
  - **App Platform の starter domain（*.ondigitalocean.app）を custom domain にリダイレクト**し、
    custom domain 側に集約する（入口制御をバイパスさせない）

---

## 8. 例外運用（必ず明文化）
- 学生に DigitalOcean 権限を渡す
- Public bucket を作る
- 参加者に閲覧権限を与える

これらは `20_OPERATING_MODEL.md` の例外ルールに従い、台帳に記録します。
