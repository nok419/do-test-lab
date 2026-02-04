from __future__ import annotations

import os
from typing import Optional

import boto3


def _s3_client():
    # DigitalOcean SpacesはS3互換のため、boto3をそのまま使えます。
    # endpoint_url はリージョンごとのS3互換エンドポイントを使います。
    endpoint_url = os.getenv("SPACES_ENDPOINT_URL")
    region = os.getenv("SPACES_REGION")

    access_key = os.getenv("SPACES_ACCESS_KEY_ID")
    secret_key = os.getenv("SPACES_SECRET_ACCESS_KEY")

    if not endpoint_url or not region:
        raise RuntimeError("SPACES_ENDPOINT_URL / SPACES_REGION is not set")
    if not access_key or not secret_key:
        raise RuntimeError("SPACES_ACCESS_KEY_ID / SPACES_SECRET_ACCESS_KEY is not set")

    return boto3.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )


def generate_presigned_upload_url(
    bucket: str, key: str, content_type: Optional[str], expires_in: int
) -> str:
    # 署名付きPUT URLを生成します。
    # 参加者がファイルをアップロードする用途では、ここをアプリ内権限で制御するのが基本です。
    client = _s3_client()

    params = {"Bucket": bucket, "Key": key}
    if content_type:
        # できるだけ意図しないファイル形式を避けたい場合に指定します。
        params["ContentType"] = content_type

    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params=params,
        ExpiresIn=expires_in,
    )


def generate_presigned_download_url(bucket: str, key: str, expires_in: int) -> str:
    # 署名付きGET URLを生成します。
    # 公開URL化するよりも、短寿命URLを都度発行する方が運用しやすい場面が多いです。
    client = _s3_client()
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
