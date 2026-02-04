# Cloudflare 導入手順（任意：DNS/Proxy/防御の標準化）

最終更新: 2026-02-03

この章は **Cloudflare を使う場合** の手順です。  
Cloudflare を使わない（DigitalOcean 管理DNSや他DNSを使う）場合は読み飛ばして構いません。

---

## 0. 先に結論（運用モード）
Cloudflare は「DNS」だけに使うことも、「Proxy（オレンジ雲）」まで使うこともできます。

### モードA（推奨・最小）：Cloudflare = DNSのみ（DNS only）
- メリット：DigitalOcean App Platform のカスタムドメイン検証/証明書発行がシンプル
- デメリット：CloudflareのWAF/Rate Limit等の機能は使えない（Proxyしていないため）

### モードB（任意・強め）：Cloudflare = DNS + Proxy（Proxied）
- メリット：WAF/Rate Limit/Access 等を入口に入れられる
- デメリット：
  - App Platform の **ドメイン検証時は DNS only が必要**になりがち
  - 二重プロキシになり得る（App Platform 自体も Cloudflare CDN を含む）
  - 障害切り分けが難しくなる

> 本書の標準は「まずモードAで安定させる」。  
> 入口防御が必要になったタイミングでモードBを段階導入します。

---

## 1. Cloudflareでゾーン（ドメイン）を追加
1. Cloudflare にログインし、対象ドメイン（例: `lab.example.org`）を追加
2. 指示された Cloudflare のネームサーバを控える
3. レジストラ（ドメイン管理会社）でネームサーバを Cloudflare に切り替える  
   - 反映に時間がかかる場合があります（DNS伝播）

---

## 2. DNSレコードの基本設計（サブドメイン）
例：
- `exp-xxx.lab.example.org` → 実験アプリ（参加者向け）
- `admin-xxx.lab.example.org` → 管理画面（必要なら）

運用上のポイント：
- 命名規則を固定し、台帳で管理する（`ops/templates/resource_inventory.csv`）

---

## 3. DigitalOcean App Platform のカスタムドメインとDNS（重要）
**手順の順番が重要です。**

### 3.1 先に DigitalOcean 側でカスタムドメインを追加
- App Platform のアプリ → Settings → Domains で、サブドメインを追加
- DigitalOcean が提示する CNAME 先（例: `<app>.ondigitalocean.app`）を控える

### 3.2 Cloudflare DNSに CNAME を作る（最初は DNS only 推奨）
- Record type: CNAME
- Name: `exp-xxx`（例）
- Target: `<app>.ondigitalocean.app`
- Proxy status: **DNS only（グレー雲）** ← まずはこれ

理由：
- ドメイン検証や証明書発行の段階では、Cloudflare Proxy があると検証が失敗することがあります。

### 3.3 DigitalOcean 側で “Verified / SSL Active” になるまで待つ
- DigitalOcean がドメインを検証し、Let’s Encrypt 証明書を自動発行します
- ブラウザで `https://exp-xxx.lab.example.org/health` が 200 になればOK

---

## 4. （任意）Proxy（オレンジ雲）を有効にする場合
必要性（WAF/Rate Limit/Access）が出た場合のみ実施します。

### 4.1 切り替え手順
1. まず **動作確認の時間帯** を決める（実験中は避ける）
2. Cloudflare DNS の Proxy status を **Proxied（オレンジ雲）** に変更
3. 以下を確認：
   - `https://exp-xxx.../health` が 200
   - WebSocket を使う場合は接続できる
   - POST/アップロード導線が問題ない（レート制限・ボット対策が邪魔しない）

### 4.2 うまくいかないとき
- まず DNS only に戻して切り分け（入口の問題かアプリの問題か）
- TLSエラー（525/526等）が出る場合：
  - Cloudflare 側 SSL/TLS mode を **Full (strict)** にするのは「Origin が正しい証明書を返す」前提です
  - DigitalOcean 側で SSL Active を確認してから実施します

---

## 5. Cloudflare 側の最低限設定（Proxyを使う場合のみ）
- HTTPSリダイレクト（Always Use HTTPS）
- Rate Limit（最低限）
  - `/auth/login`
  - `/signed-upload-url` `/signed-download-url`
- WAF（可能な範囲で）
- Bot対策（必要なら、参加者導線に影響するため段階導入）

---

## 6. 障害対応のメモ（運用として残す）
各アプリについて、以下を台帳に残します：
- サブドメイン
- DigitalOcean の CNAME 先（`<app>.ondigitalocean.app`）
- Proxy の ON/OFF
- 追加した WAF/Rate Limit ルール

障害時の具体的手順は `140_RUNBOOKS.md` を参照してください。
