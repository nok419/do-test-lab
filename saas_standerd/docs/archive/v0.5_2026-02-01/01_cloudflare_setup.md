# Cloudflare 初期設定（入口の標準化）

狙い：
- DNS/TLS/簡易防御を **研究室共通** に寄せる
- 学生アプリは「アプリ本体」に集中できる（入口設定は毎回やらない）

---

## 1) ドメイン（ゾーン）を追加
1. Cloudflareで対象ドメイン（例: `lab.example.org`）を追加
2. レジストラ側でネームサーバをCloudflareに切り替える

> ここは1回だけ（以後、サブドメインを増やす運用）

---

## 2) HTTPS（強制）をON
- SSL/TLS の **Encryption mode** は可能なら **Full (strict)** を推奨  
  - Cloudflareは暗号化モードとして Full / Full (strict) を推奨しており、Full (strict) は origin 証明書の検証も行います。
- 「Always Use HTTPS」を有効化（http→https リダイレクト）

参考（公式）:
- Always Use HTTPS: https://developers.cloudflare.com/ssl/edge-certificates/additional-options/always-use-https/
- Full (strict): https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/

---

## 3) DNS（サブドメインの作り方）
運用例：
- `exp-xxx.lab.example.org` → 各アプリの公開URL
- `admin-xxx.lab.example.org` → 管理画面（必要なら）

基本はCNAMEでOK（App Platformのデフォルトドメイン `*.ondigitalocean.app` に向ける）。

- レコード: `exp-xxx` / type: CNAME / target: `<your-app>.ondigitalocean.app`
- Proxy状態: 基本は **Proxied（オレンジ雲）**

---

## 4) 最低限の防御（コストを増やさずに）
最小は「まずこれだけ」：
- Cloudflare側の **DDoS/TLS/DNS** を使う
- さらに必要ならアプリ側で
  - `/auth/login` 等にレート制限（IP単位）
  - 参加者向けフォームに Turnstile（無料）を検討

Turnstile（公式）: https://developers.cloudflare.com/turnstile/plans/

---

## 5) 研究室メンバーだけがアクセスできる管理画面（必要な場合）
要件「データ閲覧は研究室内に限る」を強くしたい場合、選択肢は2つ：

A. **アプリ側** でRBAC（推奨：基本形）
- 参加者は参加者用ページだけ
- 研究室メンバーはログイン後にデータ閲覧できる

B. **Cloudflare側** で追加ガード（さらに固く）
- Cloudflare Access等で `/admin` を研究室アカウントだけに限定
- ただしユーザ課金が発生し得るので「必要になったら」導入

