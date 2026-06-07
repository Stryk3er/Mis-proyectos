import Anthropic from '@anthropic-ai/sdk';
import express from 'express';
import rateLimit from 'express-rate-limit';
import cookieParser from 'cookie-parser';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json({ limit: '20mb' }));
app.use(cookieParser());
app.use(express.static(join(__dirname, 'public')));

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── MODELOS Y COSTOS ──────────────────────────────────────────────
const MODELS = {
  analysis: process.env.ANALYSIS_MODEL || 'claude-sonnet-4-6',
  chat:     'claude-haiku-4-5-20251001',
};

const COST_PER_M = {
  'claude-sonnet-4-6':        { input: 3.0,  output: 15.0 },
  'claude-haiku-4-5-20251001':{ input: 0.80, output: 4.0  },
};

// ── CACHÉ EN MEMORIA ──────────────────────────────────────────────
const CACHE_TTL_MS = 60 * 60 * 1000;
const analysisCache = new Map();

function hashStr(str) {
  let h = 0;
  for (let i = 0; i < Math.min(str.length, 4000); i++) {
    h = Math.imul(31, h) + str.charCodeAt(i) | 0;
  }
  return Math.abs(h).toString(36);
}

function getCached(key) {
  const entry = analysisCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > CACHE_TTL_MS) { analysisCache.delete(key); return null; }
  return entry;
}

// ── TRACKER DE USO ────────────────────────────────────────────────
const usage = {
  totalRequests: 0,
  cacheHits:     0,
  totalInputTokens:  0,
  totalOutputTokens: 0,
  estimatedCostUSD:  0,
  byModel: {},
};

function trackUsage(model, inputTokens, outputTokens) {
  const cost = COST_PER_M[model] || COST_PER_M['claude-sonnet-4-6'];
  const usd = (inputTokens * cost.input + outputTokens * cost.output) / 1_000_000;
  usage.totalRequests++;
  usage.totalInputTokens  += inputTokens;
  usage.totalOutputTokens += outputTokens;
  usage.estimatedCostUSD  += usd;
  if (!usage.byModel[model]) usage.byModel[model] = { requests: 0, costUSD: 0 };
  usage.byModel[model].requests++;
  usage.byModel[model].costUSD += usd;
  return usd;
}

// ── AUDIT LOG ─────────────────────────────────────────────────────
const LOG_DIR = join(__dirname, 'logs');
fs.mkdirSync(LOG_DIR, { recursive: true });

function auditLog(event, actor = 'system', data = {}) {
  const entry = { ts: new Date().toISOString(), event, actor, ...data };
  try {
    fs.appendFileSync(join(LOG_DIR, 'audit.jsonl'), JSON.stringify(entry) + '\n');
  } catch (e) {
    console.error('[audit] error al escribir log:', e.message);
  }
}

// ── AUTENTICACION JWT ─────────────────────────────────────────────
const DATA_DIR   = join(__dirname, 'data');
const USERS_FILE = join(DATA_DIR, 'users.json');
const JWT_SECRET  = process.env.JWT_SECRET || 'datamind-dev-secret-CHANGE-IN-PROD';
const JWT_EXPIRES = '8h';

fs.mkdirSync(DATA_DIR, { recursive: true });

function loadUsers() {
  try { return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8')); } catch { return {}; }
}
function saveUsers(u) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(u, null, 2));
}

// Crear usuario admin al primer arranque
let users = loadUsers();
if (Object.keys(users).length === 0) {
  const adminUser = process.env.ADMIN_USER || 'admin';
  const adminPass = process.env.ADMIN_PASS || 'admin1234';
  users[adminUser] = {
    id: adminUser,
    username: adminUser,
    passwordHash: bcrypt.hashSync(adminPass, 10),
    role: 'admin',
    createdAt: new Date().toISOString(),
  };
  saveUsers(users);
  console.log(`  ✓ Usuario admin creado: "${adminUser}" / "${adminPass}" — cambia esto en prod`);
}

// Middleware: JWT en cookie httpOnly
function requireAuth(req, res, next) {
  const token = req.cookies?.token;
  if (!token) return res.status(401).json({ error: 'No autenticado' });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.clearCookie('token');
    res.status(401).json({ error: 'Sesion expirada' });
  }
}

// Middleware: solo admin
function requireAdmin(req, res, next) {
  if (req.user?.role !== 'admin') return res.status(403).json({ error: 'Solo administradores' });
  next();
}

// ── RATE LIMITING (por usuario, no por IP) ────────────────────────
const analysisLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 10,
  keyGenerator: (req) => req.user?.id || req.ip,
  message: { error: 'Limite de analisis alcanzado. Maximo 10 por hora por usuario.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const chatLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 60,
  keyGenerator: (req) => req.user?.id || req.ip,
  message: { error: 'Limite de chat alcanzado. Maximo 60 mensajes por hora por usuario.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { error: 'Demasiados intentos. Espera 15 minutos.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// ── LIMITE DE PAYLOAD ─────────────────────────────────────────────
const MAX_PROMPT_CHARS = 400_000;

// ── ENDPOINTS DE AUTH ─────────────────────────────────────────────

app.post('/api/auth/login', loginLimiter, (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'Usuario y contrasena requeridos' });

  users = loadUsers();
  const user = users[username];
  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    auditLog('login_failed', username, { ip: req.ip });
    return res.status(401).json({ error: 'Usuario o contrasena incorrectos' });
  }

  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES }
  );

  res.cookie('token', token, {
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 8 * 60 * 60 * 1000,
    // secure: true,  // descomentar con HTTPS
  });

  auditLog('login_success', username, { ip: req.ip, role: user.role });
  res.json({ username: user.username, role: user.role });
});

app.post('/api/auth/logout', requireAuth, (req, res) => {
  auditLog('logout', req.user.username, { ip: req.ip });
  res.clearCookie('token');
  res.json({ ok: true });
});

app.get('/api/auth/me', requireAuth, (req, res) => {
  res.json({ username: req.user.username, role: req.user.role });
});

app.post('/api/auth/users', requireAuth, requireAdmin, (req, res) => {
  const { username, password, role = 'analyst' } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'username y password requeridos' });
  if (users[username]) return res.status(409).json({ error: 'El usuario ya existe' });

  users[username] = {
    id: username, username,
    passwordHash: bcrypt.hashSync(password, 10),
    role, createdAt: new Date().toISOString(),
  };
  saveUsers(users);
  auditLog('user_created', req.user.username, { newUser: username, role, ip: req.ip });
  res.status(201).json({ username, role });
});

app.get('/api/auth/users', requireAuth, requireAdmin, (_req, res) => {
  const list = Object.values(loadUsers()).map(u => ({
    username: u.username, role: u.role, createdAt: u.createdAt,
  }));
  res.json(list);
});

// ── ENDPOINT: ANÁLISIS ────────────────────────────────────────────
app.post('/api/analyze', requireAuth, analysisLimiter, async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) return res.status(400).json({ error: 'prompt requerido' });

  if (prompt.length > MAX_PROMPT_CHARS) {
    return res.status(413).json({
      error: `Dataset demasiado grande (${(prompt.length / 1000).toFixed(0)}K chars). Maximo ${MAX_PROMPT_CHARS / 1000}K. Filtra columnas o usa un subconjunto de filas.`,
    });
  }

  const cacheKey = hashStr(prompt);
  const cached = getCached(cacheKey);
  if (cached) {
    usage.cacheHits++;
    auditLog('analyze_cache_hit', req.user.username, { hash: cacheKey });
    return res.json({ content: cached.result, fromCache: true, model: cached.model });
  }

  try {
    const model = MODELS.analysis;
    const msg = await client.messages.create({
      model, max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    });

    const result  = msg.content[0].text;
    const inputT  = msg.usage.input_tokens;
    const outputT = msg.usage.output_tokens;
    const usd     = trackUsage(model, inputT, outputT);

    analysisCache.set(cacheKey, { result, ts: Date.now(), model, savedUSD: usd });

    auditLog('analyze', req.user.username, {
      model, inputTokens: inputT, outputTokens: outputT, costUSD: +usd.toFixed(4),
    });
    console.log(`[analyze] user=${req.user.username} in=${inputT} out=${outputT} cost=$${usd.toFixed(4)}`);
    res.json({ content: result, fromCache: false, model, cost: usd });

  } catch (err) {
    auditLog('analyze_error', req.user.username, { error: err.message });
    console.error('[analyze error]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── ENDPOINT: CHAT ────────────────────────────────────────────────
app.post('/api/chat', requireAuth, chatLimiter, async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) return res.status(400).json({ error: 'prompt requerido' });

  if (prompt.length > MAX_PROMPT_CHARS) {
    return res.status(413).json({ error: 'Contexto demasiado grande.' });
  }

  try {
    const model = MODELS.chat;
    const msg = await client.messages.create({
      model, max_tokens: 1024,
      messages: [{ role: 'user', content: prompt }],
    });

    const result = msg.content[0].text;
    const usd = trackUsage(model, msg.usage.input_tokens, msg.usage.output_tokens);

    auditLog('chat', req.user.username, {
      model, inputTokens: msg.usage.input_tokens, outputTokens: msg.usage.output_tokens,
      costUSD: +usd.toFixed(4),
    });
    console.log(`[chat] user=${req.user.username} in=${msg.usage.input_tokens} cost=$${usd.toFixed(4)}`);
    res.json({ content: result, model });

  } catch (err) {
    auditLog('chat_error', req.user.username, { error: err.message });
    console.error('[chat error]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── HEALTH ────────────────────────────────────────────────────────
app.get('/api/health', requireAuth, (_req, res) => {
  const hitRate = usage.totalRequests > 0
    ? ((usage.cacheHits / usage.totalRequests) * 100).toFixed(1) : '0.0';

  res.json({
    status: 'ok',
    version: '3.0',
    keyConfigured: !!process.env.ANTHROPIC_API_KEY,
    models: MODELS,
    cache: { entries: analysisCache.size, hits: usage.cacheHits, hitRate: `${hitRate}%`, ttlMinutes: CACHE_TTL_MS / 60000 },
    usage: {
      totalRequests: usage.totalRequests,
      totalInputTokens: usage.totalInputTokens,
      totalOutputTokens: usage.totalOutputTokens,
      estimatedCostUSD: +usage.estimatedCostUSD.toFixed(4),
      byModel: usage.byModel,
    },
    timestamp: new Date().toISOString(),
  });
});

// ── FALLBACK SPA ──────────────────────────────────────────────────
app.get('*', (_req, res) => {
  res.sendFile(join(__dirname, 'public', 'index.html'));
});

// ── START ─────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`
  ╔══════════════════════════════════════════╗
  ║       DataMind AI  v3.0                  ║
  ║  → http://localhost:${PORT}               ║
  ╠══════════════════════════════════════════╣
  ║  Analisis : ${MODELS.analysis.padEnd(26)}║
  ║  Chat     : ${MODELS.chat.padEnd(26)}║
  ║  API key  : ${process.env.ANTHROPIC_API_KEY ? '✓ configurada            ' : '✗ falta en .env          '}║
  ║  Auth     : JWT httpOnly cookie          ║
  ║  Audit    : logs/audit.jsonl             ║
  ╚══════════════════════════════════════════╝
  `);
});
