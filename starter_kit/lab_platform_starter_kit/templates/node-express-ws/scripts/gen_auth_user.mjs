#!/usr/bin/env node
import crypto from "crypto";

const PBKDF2_ITERATIONS = 200_000;
const PBKDF2_SALT_BYTES = 16;
const PBKDF2_DKLEN = 32;
const PBKDF2_DIGEST = "sha256";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const val = argv[i + 1];
    out[key] = val;
    i++;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
if (!args.username || !args.password || !args.role) {
  console.error("usage: gen_auth_user.mjs --username <u> --password <p> --role <role>");
  process.exit(2);
}

const salt = crypto.randomBytes(PBKDF2_SALT_BYTES);
const dk = crypto.pbkdf2Sync(
  Buffer.from(String(args.password), "utf-8"),
  salt,
  PBKDF2_ITERATIONS,
  PBKDF2_DKLEN,
  PBKDF2_DIGEST
);

const entry = {
  username: String(args.username),
  role: String(args.role),
  salt_b64: salt.toString("base64"),
  hash_b64: dk.toString("base64"),
  pbkdf2_iterations: PBKDF2_ITERATIONS,
};

process.stdout.write(JSON.stringify(entry));
process.stdout.write("\n");
