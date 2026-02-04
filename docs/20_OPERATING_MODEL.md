# 運用モデル（運用境界・権限・責任分界）

最終更新: 2026-02-03

この章は **「誰が何を触るか」** を明確にして、セキュリティ事故と運用破綻を防ぐためのものです。
研究室運用は「人が入れ替わる」前提なので、権限と責任を曖昧にしないことが重要です。

---

## 1. 役割（ロール）定義

### 1.1 Platform Owner（予算責任者）
- 研究室の教員/代表者など
- 予算上限、運用ポリシー、例外許可（学生にDO権限を渡す等）の承認
- 重大インシデント時の最終判断（公開停止・外部連絡 等）

### 1.2 Platform Ops（運用チーム）
- DigitalOcean / Cloudflare の設定と保守
- 監視・バックアップ・復旧訓練の実施
- 予算監視（Billing alert、台帳、棚卸し）
- アプリ担当からの依頼に基づく、標準リソースの払い出し（DB/Spaces/Domain）

### 1.3 App Owner（アプリ担当：学生/研究員）
- アプリ実装、実験フロー設計、アプリ層セキュリティ（認証/RBAC）
- データの取り扱い（収集項目、保存先、保持期間、削除）
- 障害時の一次切り分け（アプリのバグ/設定ミス）

### 1.4 Data Steward（データ管理責任：任意）
- IRB/倫理、個人情報の取扱い、公開情報の確認
- 「収集項目と利用目的」の整合チェック

---

## 2. 権限境界（触ってよい範囲）

結論（推奨）：**DigitalOcean/Cloudflare は Platform Ops が保持し、学生は GitHub まで**。

### 2.1 推奨モデル（標準）
- **学生（App Owner）**
  - GitHub: リポジトリ作成/コード管理（ただしSecretsは置かない）
  - 依頼: DB/Spaces/Domain の払い出しは `ops/templates/experiment_request.md` で申請
- **Platform Ops**
  - DigitalOcean: Team/Project/Apps/DB/Spaces/Monitoring/Billing
  - Cloudflare（使う場合）: DNS/TLS/（必要に応じて）WAF/Rate Limit
  - Secrets: App Platform の暗号化環境変数に投入（取り扱い手順は `120_SECURITY_BASELINE.md`）

この境界にする理由：
- 学生の離脱（卒業）で権限管理が崩れない
- Secrets/コスト/削除権限の事故確率を下げる
- 運用チームの責任範囲が明確になる

### 2.2 例外モデル（学生にもDigitalOcean権限を付与する場合）
どうしても学生が App Platform を触る必要がある場合の条件：

- 例外は **Platform Owner が承認**し、台帳に明記
- DigitalOcean Team には **2FA必須**、可能ならSSO
- 変更は原則 PR/Issue を介し、運用チームがレビュー（少なくとも production は）
- Secrets は **App Platform の Encrypt 以外に置かない**
- 実験終了時に **権限剥奪/リソース整理** を必ず実施

---

## 3. RACI（責任分担の最小表）
| 作業 | Platform Owner | Platform Ops | App Owner |
|---|---|---|---|
| 予算上限/方針決定 | A | C | I |
| DigitalOcean Team/Project作成 | I | A/R | I |
| Billing alert/連絡先設定 | I | A/R | I |
| Spaces/DBの作成 | I | A/R | C |
| アプリ実装（認証/RBAC含む） | I | C | A/R |
| Smoke Test デプロイ/合格判定 | I | A/R | C |
| production go-live 判定 | A | R | R |
| 障害対応（一次） | I | R | R |
| 復旧（DB restore 等） | I | A/R | C |
| 実験終了・アーカイブ/削除 | A | R | R |

A=Accountable（最終責任） / R=Responsible（実行責任） / C=Consulted（相談） / I=Informed（共有）

---

## 4. 運用フロー（標準）

### 4.1 新規実験アプリの開始（払い出しフロー）
1. App Owner が `ops/templates/experiment_request.md` を埋める  
2. Platform Ops がレビュー（データ種別/公開範囲/保持期間/コスト）  
3. Platform Ops が払い出し：
   - サブドメイン予約
   - DBユーザ/DB作成（接続文字列）
   - Spacesバケット/キー
   - App Platform app を作成（またはAppSpec適用）
4. App Owner が実装・動作確認  
5. `starter_kit/.../docs/go_live_checklist.md` で go-live チェック  
6. production モードに移行（変更凍結の取り決め）

### 4.2 変更管理（production）
- production 中は「緊急修正」以外の変更を避ける  
- 緊急修正が必要な場合：
  - 影響範囲（参加者導線/データ欠損）を明確化
  - デプロイ前にバックアップ確認（`100_BACKUP_RESTORE.md`）

### 4.3 実験終了（archive）
- `150_OFFBOARDING.md` の手順でアーカイブ/停止/削除を実施
- 台帳を更新し、不要課金を止める

---

## 5. 連絡経路（最低限）
- 通知先（推奨）：
  - DigitalOcean Team Contact Email（運用チームの共同メアド）  
  - Platform Owner（Billing系）
- エスカレーション：
  - 参加者影響あり → Platform Ops + App Owner  
  - データ漏えい疑い → Platform Owner（即時） + Platform Ops

連絡先の具体手順は `60_SETUP_DIGITALOCEAN.md` に記載します。
