# リファレンスアーキテクチャ（標準スタック）

最終更新: 2026-02-03

---

## 1. 標準スタック（結論）
- Compute: **DigitalOcean App Platform**
- DB: **DigitalOcean Managed PostgreSQL**
- Object Storage: **DigitalOcean Spaces（S3互換）**
- Monitoring: **App Platform Alerts + Uptime（外形監視）**
- Edge（任意）: **Cloudflare（DNS/Proxy/WAF/Rate Limit）**

> 重要：App Platform 自体が Cloudflare を使った CDN を内蔵しています。  
> そのため「Cloudflare をさらに前段に置く」場合は、二重のCDN/プロキシになる可能性があります。  
> 本書では Cloudflare を **“任意（必要なら）”** に位置付け、無理に必須化しません。

---

## 2. 全体図（データフロー）
```mermaid
flowchart LR
    U[参加者ブラウザ] -->|HTTPS| E[Edge: (任意) Cloudflare]
    E -->|HTTPS| AP[DigitalOcean App Platform]
    AP -->|SQL| PG[Managed PostgreSQL]
    AP -->|署名付きURL発行| U
    U -->|PUT/GET| S[Spaces (S3互換)]
```

ポイント：
- 参加者のファイルは **署名付きURL** で Spaces へ直接アップロード（アプリ帯域を節約）
- DB は **Trusted Sources** を有効にし、アプリ以外からのアクセスを絞る
- アプリの永続は DB/Spaces のみ（アプリコンテナは捨てられる前提）

---

## 3. ドメイン設計（標準）
### 3.1 サブドメイン命名規則（例）
- 参加者向け: `exp-<slug>.lab.example.org`
- 管理/研究者向け: `admin-<slug>.lab.example.org`（必要なら）

### 3.2 “管理画面”の守り方（選択肢）
- **推奨A（簡単）**: 管理画面もアプリ内認証（RBAC）で守る
- **推奨B（強め）**: 入口で追加防御（Cloudflare Access/Basic Auth/制限）  
  ※ Cloudflare Proxy を使う場合は `50_SETUP_CLOUDFLARE.md` の注意事項に従う

---

## 4. 環境（test / production / archive）
- test:
  - 学内デモ、短期検証
  - 監視は最小、費用を最小化
- production:
  - 参加者募集を伴う実験
  - 監視・バックアップ・復旧訓練を必須
  - 変更凍結（原則）
- archive:
  - 実験終了
  - 再デプロイ可能な状態を残しつつ停止/縮退

---

## 5. 研究室で守るべき“不変条件”
- **Secrets を Git / 共有ドキュメントに置かない**  
  → App Platform の Encrypt 環境変数へ
- **復旧手順は本番前に1回通す**  
  → バックアップがあっても戻せなければ意味がない
- **コストは“上限”を運用で担保する**  
  → Billing alert + 台帳 + 棚卸し
