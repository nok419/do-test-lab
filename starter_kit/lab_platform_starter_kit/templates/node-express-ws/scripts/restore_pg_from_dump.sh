#!/usr/bin/env bash
set -euo pipefail

# 目的：
# - Spacesに退避した pg_dump を復元し、復旧訓練/障害対応に使います。
#
# 注意：
# - 既存DBに上書き復元するのは危険です。原則「新しいDBに復元して切り替え」を推奨します。

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${SPACES_BUCKET:?SPACES_BUCKET is required}"
: "${SPACES_ENDPOINT_URL:?SPACES_ENDPOINT_URL is required}"
: "${DUMP_OBJECT_KEY:?DUMP_OBJECT_KEY is required (ex: backups/app/20260101T000000Z.dump)}"

if [[ -z "${AWS_ACCESS_KEY_ID:-}" && -n "${SPACES_ACCESS_KEY_ID:-}" ]]; then
  export AWS_ACCESS_KEY_ID="${SPACES_ACCESS_KEY_ID}"
fi
if [[ -z "${AWS_SECRET_ACCESS_KEY:-}" && -n "${SPACES_SECRET_ACCESS_KEY:-}" ]]; then
  export AWS_SECRET_ACCESS_KEY="${SPACES_SECRET_ACCESS_KEY}"
fi

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID (or SPACES_ACCESS_KEY_ID) is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY (or SPACES_SECRET_ACCESS_KEY) is required}"

TMP="/tmp/restore.dump"
echo "download: s3://${SPACES_BUCKET}/${DUMP_OBJECT_KEY} -> ${TMP}"
aws --endpoint-url "${SPACES_ENDPOINT_URL}" s3 cp "s3://${SPACES_BUCKET}/${DUMP_OBJECT_KEY}" "${TMP}"

echo "restore to: ${DATABASE_URL}"
pg_restore --clean --if-exists --no-owner --no-acl --dbname "${DATABASE_URL}" "${TMP}"

rm -f "${TMP}"
echo "restore done"
