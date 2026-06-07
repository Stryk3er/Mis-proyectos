import Anthropic from '@anthropic-ai/sdk';
import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(express.json({ limit: '20mb' }));
app.use(express.static(join(__dirname, 'public')));

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── API proxy ──────────────────────────────────────────────────────
app.post('/api/analyze', async (req, res) => {
  const { prompt, model = 'claude-sonnet-4-6' } = req.body;
  if (!prompt) return res.status(400).json({ error: 'prompt requerido' });

  try {
    const msg = await client.messages.create({
      model,
      max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    });
    res.json({ content: msg.content[0].text });
  } catch (err) {
    console.error('[analyze error]', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Health check ───────────────────────────────────────────────────
app.get('/api/health', (_req, res) => {
  res.json({
    status: 'ok',
    model: 'available',
    keyConfigured: !!process.env.ANTHROPIC_API_KEY,
    timestamp: new Date().toISOString(),
  });
});

// ── Fallback → SPA ─────────────────────────────────────────────────
app.get('*', (_req, res) => {
  res.sendFile(join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n  DataMind AI  →  http://localhost:${PORT}`);
  console.log(`  API key:       ${process.env.ANTHROPIC_API_KEY ? '✓ configurada' : '✗ no encontrada — revisa .env'}\n`);
});
