# 研究室Webサービス運営基盤（標準案）：DigitalOcean + Cloudflare（改訂 v0.5 / 2026-02-01）

この文書は「長すぎて読まれない問題」を避けるため、冗長な説明を削って「技術選定の結論と理由」に寄せています。
細かい実装例（テンプレ、AppSpec雛形、バックアップスクリプト等）は `lab_platform_starter_kit/` を参照してください。

## 1. 目的（何を解決するか）
- 研究室PCを外部公開しない（DDoS等の“矛先”を研究室ネットワークから外す）
- 少人数の運営チームで、複数の実験アプリを「常駐・復旧可能」に運用できる標準を作る
- 参加者データは「URLを知っていればアクセスできる」前提では守れないため、アプリ側の認証+RBACを必須にする

## 2. 前提（運用ポリシーの最小セット）
- 可用性：実験中は原則停止しない（落ちる/消える前提の運用にしない）
- 予算目安：月額上限 100 USD、同時稼働 3件（必要なら追加申請）
- 公開範囲：URL自体は通常公開（参加者データは認証+RBACで制御）
- 稼働モード
  - test：試作/短時間デモ。落ちてもよいがデータは保全する
  - production：参加者を募集して実験を回す。常駐、監視、バックアップ、原則変更凍結
  - archive：再デプロイ可能な状態を保持し、運用コストを下げる（アプリ停止/Archive）
- データ保持：実験終了後 90日保持。以降は「削除OK」の明示があるものだけ削除

## 3. 結論：標準スタック
- Edge（標準）：Cloudflare（DNS + Proxy + WAF/Rate Limit 等）
- Compute（標準）：DigitalOcean App Platform
- DB（標準）：DigitalOcean Managed PostgreSQL
- ファイル（標準）：DigitalOcean Spaces（S3互換）
- 監視（標準）：App Platform Alerts + DigitalOcean Uptime（外形監視）
- バックアップ（標準）：Managed DBの自動バックアップ + 日次 `pg_dump` をSpacesへ退避

※ ここでの「セキュリティ」は “クラウドが全部守る” ではなく、次の分業を前提とします。
- Edge（Cloudflare）：大量アクセス/ボット/雑な攻撃の吸収、入口の共通防御
- 運営（DO）：最小権限、鍵管理、バックアップ/復旧、監視
- アプリ：認証/RBAC、レート制限、入力検証、ログ設計（個人情報を出さない）

## 4. なぜこの選定か（技術選定の説明）

### 4.1 DigitalOcean App Platformを標準にする理由
- 「Git連携で動く箱」を先に固定すると、運用の認知負荷が下がる（作り方が毎回変わらない）
- ヘルスチェック/自動再起動/ログ/スケール（固定）など、常駐運用の要点が揃っている
- ローカルディスク前提の設計を避けやすく、再デプロイ（復旧/移管）がしやすい

### 4.2 Cloudflareを前段に置く理由（研究室PCを守る土壌として）
- DNSと入口（Proxy）を統一でき、アプリが増えても運用が増えにくい
- DDoS/ボット/機械的なスキャンに対して “まず入口で落とす” を共通化できる
- Rate Limit、WAFルール、チャレンジ/Turnstile等をアプリ横断で適用できる

### 4.3 AWSと比べたときの位置づけ（短く）
- AWSはIAMやWAF等の選択肢が豊富で強力だが、運用の選択肢も増えるため「少人数運営」だと迷いが増えやすい
- 本標準は「まず実験が止まらない土壌を、速く揃える」ことを優先する
- 将来の移行余地のため、S3互換（Spaces）/コンテナ/AppSpecのような“移しやすい形”を維持する

## 5. 例外パス（標準から外す条件）
次に該当する場合は、Droplet/DOKS等へ移行（または最初から例外扱い）します。運用コストは上がります。
- WebSocketで「強いリアルタイム性」かつ「多重化が必須」で、ステートレス化/共有ストア導入でも要件を満たせない
- GPU推論を常設で回す必要がある

## 6. 標準設計原則（アプリに課す“最低限の契約”）
- 状態（データ）は外に出す
  - DB：Managed PostgreSQL
  - ファイル：Spaces
- アプリは交換可能にする
  - アプリのローカルディスクに依存しない（再デプロイで同じ状態に戻せる）
- 監視のために `/health` を提供する（HTTP 200）
- 参加者の大容量アップロード/ダウンロードは、可能な限りSpaces直（署名付きURL）に寄せる
- シークレットはGitに入れない（App Platformの暗号化環境変数で渡す）
- ログはstdout/stderrへ（障害時の切り分けを最小化）

### 6.1 WebSocketを含む場合の注意（安定稼働とスケールの両立）
- WebSocket（特にSocket.IO）は、アプリがインメモリ状態に依存すると「2インスタンス化」で事故りやすい
- 方針（標準）
  - WebSocketが必須のアプリは、原則 1インスタンス固定で開始する（まず安定動作）
  - 2インスタンス化が必要になったら、次のいずれかを採用する
    - アプリをステートレス化（トークン、外部ストア）
    - Redis等の共有ストアを導入（Socket.IO adapter 等）
    - それでも無理なら例外パス（Droplet/DOKS）へ移行

## 7. 権限設計（どこで分けるか）

### 7.1 DigitalOceanの権限（運営のための最小セット）
- DigitalOceanを操作できるのは少人数（教授 + 運営チーム）に閉じる
- App Platformの暗号化環境変数は、コンソールにアクセスできる人には見えてしまう前提で設計する

### 7.2 アプリの権限（参加者データを守る本丸）
- 参加者データ等の閲覧・操作はアプリ側で認証 + RBACを実装する
- 標準ロール（最小構成の推奨）
  - admin：ユーザ/権限付与、設定変更、エクスポート/削除など強い操作
  - researcher：データ閲覧・ダウンロード・解析
  - participant：データ投稿のみ（閲覧不可を基本）
  - assistant：運用補助（必要なら）。不要なら `researcher` に統合でOK

## 8. 導入チェックリスト（短縮）

### 8.1 Cloudflare（標準エッジ）
- DNSをCloudflareへ移管し、各アプリのサブドメインをCloudflare Proxy配下に置く
- SSL/TLSは「HTTPS必須」を前提にし、Origin（DO）側もHTTPSで受ける構成にする
- Rate Limit/WAFの最低限を入れる（ログイン、ファイル発行系、WebSocket接続エンドポイント等）
- bot対策が必要ならTurnstile等を採用（必要な範囲だけ）

詳細な手順は `lab_platform_starter_kit/docs/cloudflare_edge_checklist.md` を参照。
production開始前の最低限チェックは `lab_platform_starter_kit/docs/go_live_checklist.md` を参照。

### 8.2 DigitalOcean（標準インフラ）
- Team作成、権限、2FA（学生全員を招待しない）
- Spaces：バケット命名規則、Private、バージョニングON、バケット単位でLimited access key発行
- Managed PostgreSQL：プロジェクト単位でDB/Userを分離（必要ならHA検討）
- App Platform：AppSpecまたはコンソールで作成し、`/health` をhealth checkに設定
- バックアップ：Jobで日次 `pg_dump` -> Spaces。復旧手順を実験前に1回通す
- 監視：Alerts + Uptime（productionは必須）

## 参考リンク
- DigitalOcean App Platform
  - SLA: https://www.digitalocean.com/sla/app-platform
  - Health checks: https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/
  - Scaling: https://docs.digitalocean.com/products/app-platform/how-to/scale-app/
  - Jobs: https://docs.digitalocean.com/products/app-platform/how-to/manage-jobs/
  - Archive/Restore: https://docs.digitalocean.com/products/app-platform/how-to/archive-restore/
  - Env vars (Encrypt): https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/
  - Alerts: https://docs.digitalocean.com/products/app-platform/how-to/create-alerts/
- DigitalOcean Managed Databases (PostgreSQL)
  - SLA: https://www.digitalocean.com/sla/databases
  - Restore from backups: https://docs.digitalocean.com/products/databases/postgresql/how-to/restore-from-backups/
  - Pricing: https://docs.digitalocean.com/products/databases/postgresql/details/pricing/
- DigitalOcean Spaces
  - SLA: https://www.digitalocean.com/sla/spaces
  - Versioning: https://docs.digitalocean.com/products/spaces/how-to/enable-versioning/
  - Pricing: https://docs.digitalocean.com/products/spaces/details/pricing/
- DigitalOcean Teams (権限)
  - Team roles: https://docs.digitalocean.com/platform/teams/roles/
- DigitalOcean Uptime
  - Pricing: https://docs.digitalocean.com/products/uptime/details/pricing/
