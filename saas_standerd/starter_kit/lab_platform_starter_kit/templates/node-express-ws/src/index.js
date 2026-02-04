import express from "express";
import http from "http";
import { WebSocketServer } from "ws";

import { loadUsers, requireRoles, signToken, verifyPassword, verifyToken } from "./auth.js";
import { presignDownloadUrl, presignUploadUrl } from "./storage.js";

const app = express();
app.use(express.json());

// 外形監視用。ここが200を返しているかだけを見る前提です。
app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

// 認証（RBACの最小実装）
// - AUTH_USERS_JSON でユーザ定義
// - セッションは Bearer トークン
app.post("/auth/login", (req, res) => {
  const { username, password, expiresIn = 60 * 60 } = req.body ?? {};
  if (!username || !password) {
    return res.status(400).json({ error: "username and password are required" });
  }

  let users;
  try {
    users = loadUsers();
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }

  const u = users[String(username)];
  if (!u) return res.status(401).json({ error: "invalid credentials" });

  const saltB64 = u.salt_b64;
  const hashB64 = u.hash_b64;
  const role = u.role;
  if (!saltB64 || !hashB64 || !role) {
    return res.status(500).json({ error: "user entry is malformed" });
  }

  if (!verifyPassword(String(password), String(saltB64), String(hashB64))) {
    return res.status(401).json({ error: "invalid credentials" });
  }

  const token = signToken({ username: String(username), role: String(role), expiresIn: Number(expiresIn) });
  res.json({ token, expiresIn: Number(expiresIn), role: String(role) });
});

app.get("/auth/me", requireRoles(["admin", "researcher", "assistant", "participant"]), (req, res) => {
  res.json({ ok: true, user: req.user });
});

// 署名付きPUT URL（Spacesへ直接アップロード）
// デフォルトではログイン必須（ロールはプロジェクトに合わせて調整）
app.post("/signed-upload-url", requireRoles(["admin", "researcher", "assistant", "participant"]), async (req, res) => {
  const { key, contentType, expiresIn = 300 } = req.body ?? {};
  if (!key) {
    return res.status(400).json({ error: "key is required" });
  }
  try {
    const url = await presignUploadUrl({ key, contentType, expiresIn });
    res.json({ key, url, expiresIn });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

// 署名付きGET URL（Spacesから直接ダウンロード）
// デフォルトでは研究者のみ
app.get("/signed-download-url", requireRoles(["admin", "researcher", "assistant"]), async (req, res) => {
  const { key, expiresIn = 300 } = req.query ?? {};
  if (!key) {
    return res.status(400).json({ error: "key is required" });
  }
  try {
    const url = await presignDownloadUrl({ key, expiresIn: Number(expiresIn) });
    res.json({ key, url, expiresIn: Number(expiresIn) });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

// WebSocket（ws）
// - /ws?token=<Bearer token> のクエリで認証する例です
// - 必要なら "participant は送信のみ" 等のRBACをここで行ってください
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (socket, req) => {
  try {
    const url = new URL(req.url, "http://localhost");
    const token = url.searchParams.get("token");
    if (!token) {
      socket.close(1008, "missing token");
      return;
    }
    const claims = verifyToken(token);
    socket.user = claims;
  } catch (e) {
    socket.close(1008, "invalid token");
    return;
  }

  socket.send(JSON.stringify({ type: "hello", message: "connected", user: socket.user }));

  socket.on("message", (data) => {
    // サンプルとしてエコーします。必要に応じてプロトコルを設計してください。
    socket.send(data.toString());
  });
});

const port = Number(process.env.PORT || "8080");
server.listen(port, "0.0.0.0", () => {
  console.log(`listening on :${port}`);
});
