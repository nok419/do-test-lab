# 予算感（2026-02-01 時点の目安）

> 料金は変わり得ます。必ず公式ページの最新を見て調整してください。  
> この資料は「研究室で意思決定するための概算」と「コストが跳ねるポイント」を明確にする目的です。

---

## 基本の考え方
- 「アプリを増やすと増える費用」と「共通で固定の費用」を分ける
- **DBがコストの主役** になりやすい（性能/HAで跳ねる）
- まずは **最小構成で運用を回し、必要になったら増強** が安全

---

## 単価の目安（主要コンポーネント）

### Cloudflare（入口）
- Free: $0 / 月
- Pro: $20 / 月（年払い）または $25 / 月（毎月払い）
- Business: $200 / 月（年払い）または $250 / 月（毎月払い）

参考:
- https://www.cloudflare.com/plans/

---

### DigitalOcean App Platform（アプリ実行）
- Static siteのみ: Free tier（3 appsまで）
- Web service / worker を動かす場合はコンテナ課金
  - `apps-s-1vcpu-0.5gb`: $5 / 月
  - `apps-s-1vcpu-1gb-fixed`: $10 / 月
  - `apps-s-1vcpu-1gb`: $12 / 月
  - 超過転送: $0.02 / GiB

参考:
- https://www.digitalocean.com/pricing/app-platform
- https://docs.digitalocean.com/products/app-platform/details/pricing/

---

### DigitalOcean Managed PostgreSQL（研究データ）
- Single node: $15 / 月〜（1GiB RAM）
- High availability: $30 / 月の primary + $30 / 月の standby（=最低 $60 / 月〜）
- 追加ストレージ: $0.21 / GiB / 月

参考:
- https://docs.digitalocean.com/products/databases/postgresql/details/pricing/

---

### DigitalOcean Spaces（アップロード/バックアップ）
- $5 / 月（250GiB storage + 1TiB outbound transfer を含む）
- 追加ストレージ: $0.02 / GiB / 月
- 追加転送: $0.01 / GiB

参考:
- https://www.digitalocean.com/pricing/spaces-object-storage

---

### DigitalOcean Uptime（外形監視）
- 1 monitor は無料
- 追加 monitor は $1 / monitor / 月

参考:
- https://www.digitalocean.com/products/uptime-monitoring

---

## ざっくり見積もり例（研究室の目安）

### A) 最小PoC（Smoke Test 1本）
- App Platform: 1 × $5
- DB: 開発用（App Platform dev DB）を使うなら $7（本番非推奨）
- Spaces: 0〜$5（必要なら）
- Uptime: 1 monitor free
- Cloudflare: Free

**合計**: $5〜$17 / 月 程度

---

### B) 研究室の「運用ベースライン」（同時稼働3本・最安）
- App Platform: 3 × $5 = $15
- Managed PostgreSQL: $15（single node）
- Spaces: $5
- Uptime: 3 monitors（1 free + 2 paid）= $2
- Cloudflare: Free

**合計**: **$37 / 月** 程度（+転送超過など）

---

### C) 余裕を見た構成（同時稼働3本・アプリ1GB）
- App Platform: 3 × $10 = $30
- Managed PostgreSQL: $30（2GiBクラス想定）
- Spaces: $5
- Uptime: $2
- Cloudflare: Free

**合計**: **$67 / 月** 程度

---

### D) DBをHAにしたい（重要データ・落とせない）
- App Platform: 3 × $10 = $30
- Managed PostgreSQL: primary $30 + standby $30 = $60（最低）
- Spaces: $5
- Uptime: $2
- Cloudflare: Free

**合計**: **$97 / 月** 程度

---

## コストが跳ねるポイント（ここだけ注意）
- App Platformのインスタンス増（autoscale/instance_count増）
- DBをHAにする（最低でも倍）
- 画像/動画などの転送量増（CDN/ストレージ設計で抑える）
- Cloudflare Pro/Business（WAF等の要件が出たとき）

