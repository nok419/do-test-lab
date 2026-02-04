# DigitalOcean 導入手順（研究室共通基盤の確立）

最終更新: 2026-02-03

この章は **研究室共通の基盤（Team/Project/監視/バックアップの型）** を作る手順です。  
学生アプリを載せる前に、運用チームがここまでを整備します。

---

## 0. リージョン方針（先に決める）
原則：
- **App Platform / DB / Spaces を同一リージョンに寄せる**（遅延と運用を単純化）
- 実験参加者が日本中心なら、まずは **SGP（シンガポール）** を第一候補にする  
  - ただし、データ越境/学内規定/倫理審査で制約がある場合は別途検討

---

## 1. Team（研究室用）を作る
1. DigitalOcean で Team を作成（例: `lab-team`）
2. Team の Owner / Billing / Member を割り当てる  
   - Owner は運用チームの最小人数（例: 2名）に限定  
   - Billing は予算責任者（Platform Owner）を含める

### 1.1 Team Contact Email を設定（重要）
運用通知（デプロイ失敗、SSL更新通知など）の送信先になります。  
運用チームの共同メアドに設定してください。

- Team Settings → Contact Emails → Team contact email

> ここを個人メールのままにすると、担当者の卒業/異動で通知が消えます。

---

## 2. Secure Sign-In（2FA/SSO）
- 全員 2FA を必須にする（運用ルール）
- 可能なら SSO を検討（運用人数が多い場合）

---

## 3. Billing alert（請求アラート）を入れる（必須）
DigitalOcean は「指定金額を超えたらメール通知」を設定できます。  
月額上限（例: $100/月）に合わせて、2段階で設定するのがおすすめです。

例：
- 警告: $50
- 上限: $90（または $100 直前）

手順：
- Billing → Billing alerts → Enable → Amount を設定

> これは“停止する”機能ではなく、メール通知です。  
> 停止/縮退は `130_COST_GUARDRAILS.md` の運用で担保します。

---

## 4. Project を作る（整理用）
推奨：
- `lab-platform-prod`
- `lab-platform-test`

ポイント：
- Project は **権限分離ではなく整理** のために使います  
  （権限分離は Team 運用と運用ルールで担保）

---

## 5. Spaces（S3互換）を作る
### 5.1 バケット設計（推奨）
最小構成（まずはこれ）：
- `lab-prod-uploads`（参加者アップロード）
- `lab-prod-backups`（DBの論理バックアップ）
- `lab-prod-artifacts`（成果物/静的ファイルがある場合）

運用上のポイント：
- **Private を基本**（公開が必要なものだけ公開）
- バケット単位でアクセスキーを分ける（後述）

### 5.2 バケット作成と設定（最低限）
- Region を選択（例: `sgp1`）
- バケットを作成
- 可能なら **Versioning を有効化**（誤削除に強くなる）
- Public access は原則OFF（必要なケースのみ例外）

### 5.3 アクセスキー（Per-Bucket Access Keys を推奨）
- バケット単位で Read/Write を分ける  
  例：
  - アップロード用キー（Write）
  - バックアップ用キー（Write）
  - 解析用キー（Read）※必要なら

運用ルール：
- 1アプリ = 1キー（最小権限）
- キーは App Platform の Encrypt 環境変数にのみ投入

### 5.4 （必要なら）CORS
参加者がブラウザから署名付きURLで PUT する場合、CORS が必要になることがあります。  
必要になった時点で、対象バケットにだけ設定します。

---

## 6. Managed PostgreSQL を作る
### 6.1 クラスタ作成（まずは最小）
- Region は App Platform と揃える
- まずは single node / 最小サイズで開始し、必要ならスケール

### 6.2 DB/ユーザの分離（必須）
- **1アプリ = 1DBユーザ**
- 1アプリ = 1DB（または1スキーマ）  
  → 誤操作の影響範囲を小さくする

### 6.3 Trusted Sources（必須）
方針：
- DB は **Trusted Sources を有効**にし、接続元を絞る
- App Platform のアプリを Trusted Source として登録する  
  - App Platform から DB を接続設定すると、アプリが Trusted Source として追加されることがあります

開発/調査で手元から接続したい場合：
- 一時的に自分のIPを Trusted Source に追加（期限を決めて消す）
- もしくは “調査用DB” に復元して作業する（推奨）

---

## 7. DigitalOcean Uptime（外形監視）を準備
- Uptime で `/health` を監視する（1〜5分間隔）
- 通知先は Team Contact Email を基本にする

> 監視を入れる前にSmoke Testを立てるのが手順としては自然です。  
> 実際の手順は `80_SMOKETEST_STEP_BY_STEP.md` にまとめています。

---

## 8. ここまでの完了条件（Platform Ops のDone）
- [ ] Team Contact Email が共同メアドになっている
- [ ] Billing alert が設定されている
- [ ] `prod/test` の Project が作られている
- [ ] Spaces バケットが作成され、用途別に分けられている
- [ ] Per-bucket access key の払い出し方針が決まっている
- [ ] Managed PostgreSQL が作成され、Trusted Sources 運用が決まっている

次に進む：
- Smoke Test デプロイ: `80_SMOKETEST_STEP_BY_STEP.md`
