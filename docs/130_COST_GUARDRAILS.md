# コスト管理（予算上限を“運用で”守る）

最終更新: 2026-02-03

DigitalOcean は“ハード上限で停止する”タイプの予算機能ではないため、  
**アラート + 台帳 + 棚卸し + 停止/縮退** を標準運用として定義します。

---

## 1. 基本方針
- production の挙動と費用は **固定**する（スケール設定を曖昧にしない）
- 実験終了後は **必ず archive/停止**する（放置が最大のコスト増）
- 課金の見える化は「台帳」で担保する（人が変わっても追える）

---

## 2. 仕組み（最低限）
### 2.1 Billing alert（必須）
- `60_SETUP_DIGITALOCEAN.md` の手順で設定
- 2段階（警告/上限）推奨

### 2.2 台帳（必須）
`ops/templates/resource_inventory.csv` を運用する。

最低限の列：
- app_name / status（test/production/archive）
- domain
- DB（cluster, db_name, user）
- Spaces（bucket, prefix）
- owner（App Owner）
- start_date / planned_end_date
- notes（保持期間/削除予定）

### 2.3 棚卸し（必須）
推奨：週1（小さく始めるなら隔週でも可）

棚卸しで見るもの：
- “今月もう使ってない” アプリが生きていないか
- backup job が不要に回り続けていないか
- DB/Spaces に不要なデータが溜まっていないか

---

## 3. 具体的なガードレール（標準ルール）
### 3.1 App Platform
- instance_count は基本 1
- instance_size は明示（自動で上げない）
- production は “常時稼働” 前提（落ちる前提で設計しない）

### 3.2 DB
- 最小構成で開始し、必要ならスケール
- 実験終了後は archive 方針に従って縮退/停止（方針を決める）

### 3.3 Spaces
- バケット/プレフィックスを整理して、放置された大容量データを減らす
- retention を決める（`100_BACKUP_RESTORE.md`）

---

## 4. Billing alert が鳴ったときの行動
1. 台帳で “稼働中アプリ” と “不要アプリ” を確認
2. 不要アプリを archive（App Platform 停止、job停止）
3. DB の縮退/停止（方針に従う）
4. Spaces の不要データ/バックアップ世代の整理
5. 予算責任者へ報告（原因と対策）

---

## 5. “放置” を防ぐ仕組み（おすすめ）
- 新規アプリの申請時に「終了予定日」を必須にする（`experiment_request.md`）
- 終了予定日の1週間前に Platform Ops がリマインド
- 終了後 2週間で archive 未実施なら、Platform Owner にエスカレーション
