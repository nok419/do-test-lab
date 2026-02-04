# syntax=docker/dockerfile:1
FROM node:20-alpine

# 研究室標準の前提：
# - コンテナは「いつでも捨てられる」前提なので、永続データはDB/Spacesへ寄せます。
# - 余計なパッケージを入れずにビルド時間を抑えます。

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY src ./src

ENV PORT=8080

CMD ["node", "src/index.js"]
