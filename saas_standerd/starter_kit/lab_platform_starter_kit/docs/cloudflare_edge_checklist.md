# Cloudflare Edge Checklist（任意：DigitalOcean App Platformの前段）

最終更新: 2026-02-03

このチェックリストは「Cloudflareを使うなら、最低限どこまで揃えるか」をまとめたものです。

> 注意：DigitalOcean App Platform 自体が Cloudflare CDN を内蔵しています。  
> Cloudflare をさらに前段に置く場合は二重プロキシになり得るため、必要性があるときだけ導入します。

---

## 0. 運用モードを選ぶ
- **モードA（推奨）**: Cloudflare = DNS only（グレー雲）
  - ドメイン検証/証明書発行がシンプル
- **モードB（任意）**: Cloudflare = Proxy（オレンジ雲）
  - WAF/Rate Limit/Access など入口防御が必要なときだけ

---

## 1. ドメイン設計
- プロジェクトごとにサブドメインを切る  
  例：`exp-a.lab.example.org`、`exp-b.lab.example.org`
- 命名規則を台帳で管理（`ops/templates/resource_inventory.csv`）

---

## 2. Cloudflareにゾーンを追加
- 対象ドメインをCloudflareに追加
- レジストラ側のネームサーバをCloudflare指定のものへ変更

---

## 3. DigitalOcean側でカスタムドメインを追加
- App Platform の各アプリにサブドメインを追加
- DigitalOcean が提示する CNAME 先を控える

---

## 4. Cloudflare DNSを設定
- Cloudflare DNS に CNAME を追加
- **まずは DNS only（推奨）**  
  → DigitalOcean 側で Verified / SSL Active を確認
- （必要なら）Proxy を ON にして動作確認  
  → 問題が出たら DNS only に戻して切り分け

---

## 5. 入口防御（Proxyを使う場合のみ）
- HTTPS強制（Always Use HTTPS 等）
- Rate Limit（最低限）
  - `/auth/login`
  - `/signed-upload-url` `/signed-download-url`
  - WebSocket `/ws`（使う場合）
- WAF/ボット対策は段階導入（参加者導線に影響するため）

---

## 6. 記録
- Proxy ON/OFF
- 追加したルール（Rate Limit/WAF）
- 例外運用（参加者導線への影響があった等）

記録は台帳に残します。
