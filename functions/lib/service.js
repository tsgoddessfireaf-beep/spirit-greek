// The whole reading flow, with its outside helpers passed in so tests can run it with no
// network and no accounts: client (Claude), store (the database), log.
'use strict';

const crypto = require('crypto');
const { validateRequest, buildPacket } = require('./packet');
const { SYSTEM, userMessage } = require('./prompt');
const { parseReply, checkReading } = require('./checks');

const MODEL = 'claude-sonnet-5-5';
const MAX_TOKENS = 1800;
const ATTEMPTS = 2; // one try, one retry

const hash = (token) => crypto.createHash('sha256').update(token).digest('hex');

async function askClaude(client, packet, problems) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: MAX_TOKENS,
    system: SYSTEM,
    messages: [{ role: 'user', content: userMessage(packet, problems) }],
  });
  const text = (response.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
  return { text, usage: response.usage || {} };
}

// Waite's words for each card, shown under (or instead of) the written reading.
function passages(packet) {
  return packet.cards.map((c) => ({
    position: c.position,
    positionName: c.positionName,
    card: c.name,
    orientation: c.orientation,
    text: c.meaning ? c.meaning.text : null,
    where: c.meaning ? c.meaning.where : null,
    status: c.meaning ? c.meaning.status : null,
    noReversedMeaning: c.noReversedMeaning,
  }));
}

async function runReading({ body, lib, client, store, log = () => {}, newId = () => crypto.randomUUID(), newToken = () => crypto.randomBytes(24).toString('hex') }) {
  const request = validateRequest(body);
  const packet = buildPacket(lib, request);

  let problems = [];
  let reading = null;
  const usage = { input_tokens: 0, output_tokens: 0 };
  for (let attempt = 1; attempt <= ATTEMPTS && !reading; attempt += 1) {
    const { text, usage: u } = await askClaude(client, packet, problems);
    usage.input_tokens += u.input_tokens || 0;
    usage.output_tokens += u.output_tokens || 0;
    const reply = parseReply(text);
    problems = checkReading(reply, packet, lib.cards);
    if (!problems.length) reading = { intro: reply.intro, cards: reply.cards.map((c) => ({ position: c.position, text: c.text })), summary: reply.summary };
  }

  // The question is saved only with a clear yes, and only when there is a question.
  let saved = null;
  if (request.consent && request.question) {
    const id = newId();
    const deleteToken = newToken();
    await store.save(id, {
      question: request.question,
      spread: request.spread,
      cards: request.cards,
      createdAt: new Date().toISOString(),
      deleteTokenHash: hash(deleteToken),
    });
    saved = { id, deleteToken };
  }

  // Logged: spread, card numbers, tokens, outcome. Never the question.
  log({ spread: request.spread, cards: request.cards.map((c) => c.card), mode: reading ? 'ai' : 'quotes', usage, saved: Boolean(saved) });

  return {
    mode: reading ? 'ai' : 'quotes',
    reading,
    passages: passages(packet),
    recurrences: packet.recurrences,
    saved,
    notice: reading ? null : "The written reading could not be checked, so these are Waite's own words for your cards.",
  };
}

async function deleteReading({ body, store }) {
  if (!body || typeof body.id !== 'string' || typeof body.token !== 'string') return { deleted: false };
  const doc = await store.get(body.id);
  if (!doc || typeof doc.deleteTokenHash !== 'string') return { deleted: false };
  const given = Buffer.from(hash(body.token), 'hex');
  const want = Buffer.from(doc.deleteTokenHash, 'hex');
  if (given.length !== want.length || !crypto.timingSafeEqual(given, want)) return { deleted: false };
  await store.remove(body.id);
  return { deleted: true };
}

module.exports = { MODEL, runReading, deleteReading };
