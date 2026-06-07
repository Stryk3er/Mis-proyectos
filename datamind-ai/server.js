import Anthropic from '@anthropic-ai/sdk';
import express from 'express';
import rateLimit from 'express-rate-limit';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json({ limit: '20mb' }));
app.use(express.static(join(__dirname, 'public')));

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── MODELOS Y COSTOS ──────────────────────────────────────────────
// Sonnet para análisis profundo, Haiku para chat — 20x más barato
const MODELS = {
  analysis: process.env.ANALYSIS_MODEL || 'claude-sonnet-4-6',
  chat:     'claude-haiku-4-5-20251001',
};

// USD por millón de tokens (precios Anthropic, junio 2025)
const COST_PER_M = {
  'claude-sonnet-4-6':        { input: 3.0,  output: 15.0 },
  'claude-haiku-4-5-20251001':{ input: 0.80, output: 4.0  },
};

// ── CACHÉ EN MEMORIA ──────────────────────────────────────────────
// Evita re-analizar el mismo dataset → costo $0 en cache hit
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hora
const analysisCache = new Map(); // { hash → { result, ts, model } }

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

// ── RATE LIMITING ─────────────────────────────────────────────────
// Análisis: máx 10 por hora por IP (operación costosa)
const analysisLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 10,
  message: { error: 'Límite de análisis alcanzado. Máximo 10 por hora.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// Chat: máx 60 mensajes por hora por IP
const chatLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 60,
  message: { error: 'Límite de chat alcanzado. Máximo 60 mensajes por hora.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// ── ENDPOINT: ANÁLISIS (Sonnet + caché) ───────────────────────────
app.post('/api/analyze', analysisLimiter, async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) return res.status(400).json({ error: 'prompt requerido' });

  // Cache check
  const cacheKey = hashStr(prompt);
  const cached = getCached(cacheKey);
  if (cached) {
    usage.cacheHits++;
    console.log(`[analyze] CACHE HIT — ${cacheKey} (ahorrado ~$${(cached.savedUSD||0).toFixed(4)})`);
    return res.json({ content: cached.result, fromCache: true, model: cached.model });
  }

  try {
    const model = MODELS.analysis;
    const msg = await client.messages.create({
      model,
      max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    });

    const result = msg.content[0].text;
    const inputT  = msg.usage.input_tokens;
    const outputT = msg.usage.output_tokens;
    const usd = trackUsage(model, inputT, outputT);

    // Guardar en caché
    analysisCache.set(cacheKey, { result, ts: Date.now(), model, savedUSD: usd });

    console.log(`[analyze] model=${model} in=${inputT} out=${outputT} cost=$${usd.toFixed(4)}`);
    res.json({ content: result, fromCache: false, model, cost: usd });

  } catch (err) {
    console.error('[analyze error]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── ENDPOINT: CHAT (Haiku — sin caché, cada pregunta es única) ────
app.post('/api/chat', chatLimiter, async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) return res.status(400).json({ error: 'prompt requerido' });

  try {
    const model = MODELS.chat;
    const msg = await client.messages.create({
      model,
      max_tokens: 1024,
      messages: [{ role: 'user', content: prompt }],
    });

    const result = msg.content[0].text;
    const usd = trackUsage(model, msg.usage.input_tokens, msg.usage.output_tokens);

    console.log(`[chat] model=${model} in=${msg.usage.input_tokens} out=${msg.usage.output_tokens} cost=$${usd.toFixed(4)}`);
    res.json({ content: result, model });

  } catch (err) {
    console.error('[chat error]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── ENDPOINT: HEALTH + MÉTRICAS DE COSTO ─────────────────────────
app.get('/api/health', (_req, res) => {
  const hitRate = usage.totalRequests > 0
    ? ((usage.cacheHits / usage.totalRequests) * 100).toFixed(1)
    : '0.0';

  res.json({
    status: 'ok',
    keyConfigured: !!process.env.ANTHROPIC_API_KEY,
    models: MODELS,
    cache: {
      entries:  analysisCache.size,
      hits:     usage.cacheHits,
      hitRate:  `${hitRate}%`,
      ttlMinutes: CACHE_TTL_MS / 60000,
    },
    usage: {
      totalRequests:     usage.totalRequests,
      totalInputTokens:  usage.totalInputTokens,
      totalOutputTokens: usage.totalOutputTokens,
      estimatedCostUSD:  +usage.estimatedCostUSD.toFixed(4),
      byModel:           usage.byModel,
    },
    timestamp: new Date().toISOString(),
  });
});

// ── FALLBACK SPA ───────────────────────────────────────────────────
app.get('*', (_req, res) => {
  res.sendFile(join(__dirname, 'public', 'index.html'));
});

// ── START ──────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`
  ╔══════════════════════════════════════╗
  ║       DataMind AI  v2.1              ║
  ║  → http://localhost:${PORT}             ║
  ╠══════════════════════════════════════╣
  ║  Análisis : ${MODELS.analysis.padEnd(24)}║
  ║  Chat     : ${MODELS.chat.padEnd(24)}║
  ║  API key  : ${process.env.ANTHROPIC_API_KEY ? '✓ configurada          ' : '✗ falta en .env        '}║
  ╚══════════════════════════════════════╝
  `);
});
