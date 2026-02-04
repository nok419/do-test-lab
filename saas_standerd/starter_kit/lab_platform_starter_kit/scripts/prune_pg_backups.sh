#!/usr/bin/env bash
set -euo pipefail

# 目的：
# - Spaces上のバックアップ世代を削除して、コスト増を防ぎます。
# - Jobで日次/週次で回す想定です（productionは週次でも可）。
#
# 前提：
# - aws cli を利用します（S3互換）。
# - オブジェクトの最終更新時刻を基準に削除します。

: "${SPACES_BUCKET:?SPACES_BUCKET is required}"
: "${SPACES_ENDPOINT_URL:?SPACES_ENDPOINT_URL is required}"
: "${APP_NAME:?APP_NAME is required}"

: "${SPACES_BACKUP_PREFIX:=backups}"
: "${BACKUP_RETENTION_DAYS:=30}"

if [[ -z "${AWS_ACCESS_KEY_ID:-}" && -n "${SPACES_ACCESS_KEY_ID:-}" ]]; then
  export AWS_ACCESS_KEY_ID="${SPACES_ACCESS_KEY_ID}"
fi
if [[ -z "${AWS_SECRET_ACCESS_KEY:-}" && -n "${SPACES_SECRET_ACCESS_KEY:-}" ]]; then
  export AWS_SECRET_ACCESS_KEY="${SPACES_SECRET_ACCESS_KEY}"
fi
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID (or SPACES_ACCESS_KEY_ID) is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY (or SPACES_SECRET_ACCESS_KEY) is required}"

CUTOFF_EPOCH="$(date -u -d "-${BACKUP_RETENTION_DAYS} days" +%s)"
PREFIX="${SPACES_BACKUP_PREFIX}/${APP_NAME}/"

echo "prune: bucket=${SPACES_BUCKET} prefix=${PREFIX} retention_days=${BACKUP_RETENTION_DAYS} cutoff_epoch=${CUTOFF_EPOCH}"

# aws s3 ls output: YYYY-MM-DD HH:MM:SS SIZE KEY
aws --endpoint-url "${SPACES_ENDPOINT_URL}" s3 ls "s3://${SPACES_BUCKET}/${PREFIX}" --recursive | while read -r d t size key; do
  if [[ -z "${key:-}" ]]; then
    continue
  fi
  if [[ "${d}" == "PRE" ]]; then
    continue
  fi

  # Convert to epoch (requires coreutils date)
  obj_epoch="$(date -u -d "${d}T${t}Z" +%s || true)"
  if [[ -z "${obj_epoch}" ]]; then
    echo "skip (cannot parse time): ${d} ${t} ${key}"
    continue
  fi

  if (( obj_epoch < CUTOFF_EPOCH )); then
    echo "delete: s3://${SPACES_BUCKET}/${key} (epoch=${obj_epoch})"
    aws --endpoint-url "${SPACES_ENDPOINT_URL}" s3 rm "s3://${SPACES_BUCKET}/${key}"
  fi
done

echo "prune done"
