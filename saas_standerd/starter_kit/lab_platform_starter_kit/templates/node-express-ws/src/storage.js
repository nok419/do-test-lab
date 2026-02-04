import { S3Client, PutObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

// DigitalOcean SpacesはS3互換のため、AWS SDKをそのまま利用できます。
// 標準化のため、環境変数のキー名は固定します。
function getEnv(name) {
  const v = process.env[name];
  if (!v) {
    throw new Error(`${name} is not set`);
  }
  return v;
}

function s3() {
  const endpoint = getEnv("SPACES_ENDPOINT_URL"); // 例: https://nyc3.digitaloceanspaces.com
  const region = getEnv("SPACES_REGION");         // 例: nyc3

  return new S3Client({
    region,
    endpoint,
    credentials: {
      accessKeyId: getEnv("SPACES_ACCESS_KEY_ID"),
      secretAccessKey: getEnv("SPACES_SECRET_ACCESS_KEY"),
    },
  });
}

function bucket() {
  return getEnv("SPACES_BUCKET");
}

export async function presignUploadUrl({ key, contentType, expiresIn }) {
  const client = s3();
  const cmd = new PutObjectCommand({
    Bucket: bucket(),
    Key: key,
    ContentType: contentType || undefined,
  });
  return await getSignedUrl(client, cmd, { expiresIn });
}

export async function presignDownloadUrl({ key, expiresIn }) {
  const client = s3();
  const cmd = new GetObjectCommand({
    Bucket: bucket(),
    Key: key,
  });
  return await getSignedUrl(client, cmd, { expiresIn });
}
