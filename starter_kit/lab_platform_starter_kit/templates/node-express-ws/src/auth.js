import crypto from "crypto";

const PBKDF2_ITERATIONS = 200_000;
const PBKDF2_DKLEN = 32; // 256-bit
const PBKDF2_DIGEST = "sha256";

// base64url encode/decode (paddingなし)
function b64urlEncode(buf) {
  return buf
    .toString("base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

function b64urlDecode(s) {
  const padLen = (4 - (s.length % 4)) % 4;
  const padded = s + "=".repeat(padLen);
  return Buffer.from(padded.replace(/-/g, "+").replace(/_/g, "/"), "base64");
}

function getSecret() {
  const s = process.env.AUTH_TOKEN_SECRET;
  if (!s) throw new Error("AUTH_TOKEN_SECRET is not set");
  return Buffer.from(s, "utf-8");
}

export function loadUsers() {
  const raw = process.env.AUTH_USERS_JSON || "[]";
  let arr;
  try {
    arr = JSON.parse(raw);
  } catch (e) {
    throw new Error(`AUTH_USERS_JSON must be valid JSON: ${e}`);
  }
  if (!Array.isArray(arr)) throw new Error("AUTH_USERS_JSON must be a JSON array");

  /** @type {Record<string, any>} */
  const users = {};
  for (const u of arr) {
    if (!u || typeof u !== "object") continue;
    if (!u.username) continue;
    users[String(u.username)] = u;
  }
  return users;
}

export function pbkdf2Hash(password, saltB64) {
  const salt = Buffer.from(saltB64, "base64");
  const dk = crypto.pbkdf2Sync(
    Buffer.from(password, "utf-8"),
    salt,
    PBKDF2_ITERATIONS,
    PBKDF2_DKLEN,
    PBKDF2_DIGEST
  );
  return dk.toString("base64");
}

export function verifyPassword(password, saltB64, hashB64) {
  const computed = pbkdf2Hash(password, saltB64);
  // timingSafeEqual は同じ長さが必要
  const a = Buffer.from(computed, "utf-8");
  const b = Buffer.from(hashB64, "utf-8");
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

export function signToken({ username, role, expiresIn }) {
  const exp = Math.floor(Date.now() / 1000) + Number(expiresIn);
  const payload = { sub: username, role, exp };
  const payloadJson = Buffer.from(JSON.stringify(payload), "utf-8");
  const payloadB64 = b64urlEncode(payloadJson);

  const sig = crypto.createHmac("sha256", getSecret()).update(payloadB64).digest();
  const sigB64 = b64urlEncode(sig);
  return `${payloadB64}.${sigB64}`;
}

export function verifyToken(token) {
  const parts = String(token).split(".", 2);
  if (parts.length !== 2) throw new Error("token format is invalid");

  const [payloadB64, sigB64] = parts;
  const expected = crypto.createHmac("sha256", getSecret()).update(payloadB64).digest();
  const expectedB64 = b64urlEncode(expected);

  const a = Buffer.from(expectedB64, "utf-8");
  const b = Buffer.from(sigB64, "utf-8");
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    throw new Error("signature mismatch");
  }

  const payload = JSON.parse(b64urlDecode(payloadB64).toString("utf-8"));
  const exp = Number(payload.exp || 0);
  if (exp <= Math.floor(Date.now() / 1000)) throw new Error("token expired");
  return payload;
}

export function requireAuth(req, res, next) {
  const auth = req.headers["authorization"];
  if (!auth || !String(auth).startsWith("Bearer ")) {
    return res.status(401).json({ error: "missing Bearer token" });
  }
  const token = String(auth).split(" ", 2)[1]?.trim();
  try {
    req.user = verifyToken(token);
    return next();
  } catch (e) {
    return res.status(401).json({ error: `invalid token: ${e}` });
  }
}

export function requireRoles(roles) {
  return (req, res, next) => {
    requireAuth(req, res, () => {
      const role = String(req.user?.role || "");
      if (!roles.includes(role)) {
        return res.status(403).json({ error: "forbidden" });
      }
      return next();
    });
  };
}
