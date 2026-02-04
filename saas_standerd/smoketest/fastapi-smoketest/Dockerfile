# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 研究室標準の前提：
# - コンテナは「いつでも捨てられる」前提なので、永続データはDB/Spacesへ寄せます。
# - OSパッケージは必要最小限にし、攻撃面積とビルド時間を抑えます。

WORKDIR /app

# psycopg2-binary はビルドにgcc等が不要なため、学習コストを下げます。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# App Platform はPORT環境変数で待受ポートが渡る想定です。
ENV PORT=8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
