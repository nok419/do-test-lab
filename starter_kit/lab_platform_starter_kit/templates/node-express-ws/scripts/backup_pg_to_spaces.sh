#!/usr/bin/env bash
set -euo pipefail

# 目的：
# - 実験運用中に「DBが消えた」「戻せない」を避けるため、Managed DBの自動バックアップに加えて
#   日次で論理バックアップ（pg_dump）をSpacesに退避します。
#
# 前提：
# - App Platform Job など、定期実行できる環境で動かす想定です。
# - DATABASE_URL はManaged PostgreSQLの接続文字列を入れてください。
# - SpacesはS3互換のため aws cli を利用します。

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${SPACES_BUCKET:?SPACES_BUCKET is required}"
: "${SPACES_ENDPOINT_URL:?SPACES_ENDPOINT_URL is required}"

# 任意（未指定ならデフォルト）
: "${SPACES_BACKUP_PREFIX:=backups}"
: "${APP_NAME:=app}"

# Credentials:
# - aws cli は AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY を参照します。
# - ただしアプリ本体では SPACES_ACCESS_KEY_ID / SPACES_SECRET_ACCESS_KEY を使うことが多いので、
#   Job でも同名で渡した場合に自動で寄せます。
if [[ -z "${AWS_ACCESS_KEY_ID:-}" && -n "${SPACES_ACCESS_KEY_ID:-}" ]]; then
  export AWS_ACCESS_KEY_ID="${SPACES_ACCESS_KEY_ID}"
fi
if [[ -z "${AWS_SECRET_ACCESS_KEY:-}" && -n "${SPACES_SECRET_ACCESS_KEY:-}" ]]; then
  export AWS_SECRET_ACCESS_KEY="${SPACES_SECRET_ACCESS_KEY}"
fi

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID (or SPACES_ACCESS_KEY_ID) is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY (or SPACES_SECRET_ACCESS_KEY) is required}"

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OBJ_KEY="${SPACES_BACKUP_PREFIX}/${APP_NAME}/${TS}.dump"
TMP="/tmp/${APP_NAME}-${TS}.dump"

echo "backup: ${APP_NAME} -> ${TMP}"
pg_dump --format=c --no-owner --no-acl "${DATABASE_URL}" -f "${TMP}"

echo "upload: s3://${SPACES_BUCKET}/${OBJ_KEY}"
aws --endpoint-url "${SPACES_ENDPOINT_URL}" s3 cp "${TMP}" "s3://${SPACES_BUCKET}/${OBJ_KEY}"

rm -f "${TMP}"
echo "done: s3://${SPACES_BUCKET}/${OBJ_KEY}"
