// Turns a dealt reading into the "packet" Claude is given: the cards, where each one
// lies, which way up, and Waite's words for it. Every quote carries a status,
// "approved" (Dolores checked it) or "draft" (word for word from Waite, not yet checked).
'use strict';

const fs = require('fs');
const path = require('path');

const SPREAD_SIZES = { one: 1, three: 3, celtic: 10 };
const MAX_QUESTION = 500;
const DECK_SIZE = 78;
const RANKS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King'];

class RequestError extends Error {
  constructor(message) {
    super(message);
    this.statusCode = 400;
  }
}

// On the server the library is copied to ../knowledge before deploy; in tests and on
// a laptop it sits at the repository root.
function knowledgeDir() {
  for (const d of [path.join(__dirname, '..', 'knowledge'), path.join(__dirname, '..', '..', 'knowledge')]) {
    if (fs.existsSync(path.join(d, 'cards.json'))) return d;
  }
  throw new Error('Reading library not found');
}

function loadLibrary(dir = knowledgeDir()) {
  const read = (f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  return {
    cards: read('cards.json'),
    spreads: read('spreads.json'),
    rules: read('rules.json'),
    approved: new Set(Object.keys(read('verified.json').verified || {})),
  };
}

// Checks the request from the phone. Anything unexpected is refused.
function validateRequest(body) {
  if (!body || typeof body !== 'object') throw new RequestError('Request must be a JSON object');
  const size = SPREAD_SIZES[body.spread];
  if (!size) throw new RequestError('Unknown spread (use one, three or celtic)');
  if (!Array.isArray(body.cards) || body.cards.length !== size) {
    throw new RequestError(`The ${body.spread} spread needs exactly ${size} cards`);
  }
  const seen = new Set();
  const cards = body.cards.map((c) => {
    if (!c || !Number.isInteger(c.card) || c.card < 0 || c.card >= DECK_SIZE) throw new RequestError('Each card needs a card number from 0 to 77');
    if (typeof c.reversed !== 'boolean') throw new RequestError('Each card needs reversed: true or false');
    if (seen.has(c.card)) throw new RequestError('A card cannot appear twice');
    seen.add(c.card);
    return { card: c.card, reversed: c.reversed };
  });
  let question = '';
  if (body.question != null) {
    if (typeof body.question !== 'string') throw new RequestError('Question must be text');
    question = body.question.trim();
    if (question.length > MAX_QUESTION) throw new RequestError(`Question is longer than ${MAX_QUESTION} characters`);
  }
  // Saving the question needs a clear yes. Anything else counts as no.
  return { spread: body.spread, cards, question, consent: body.consent === true };
}

function rankOf(name) {
  const rank = name.split(' of ')[0];
  return name.includes(' of ') && RANKS.includes(rank) ? rank : null;
}

// Waite's meaning for 2, 3 or 4 cards of one rank in the same reading.
function recurrences(lib, dealt) {
  const counts = new Map();
  for (const d of dealt) {
    const rank = rankOf(lib.cards[d.card].name);
    if (!rank) continue;
    const key = `${rank}|${d.reversed ? 'reversed' : 'upright'}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const out = [];
  for (const item of lib.rules.recurrence.items) {
    if (counts.get(`${item.rank}|${item.orientation}`) === item.count) {
      out.push({ rank: item.rank, count: item.count, orientation: item.orientation, meaning: quote(lib, item.meaning) });
    }
  }
  return out;
}

function quote(lib, q) {
  if (!q || typeof q.text !== 'string') return null;
  return { text: q.text, where: q.where, source: q.source, status: lib.approved.has(q.id) ? 'approved' : 'draft' };
}

function buildPacket(lib, request) {
  const spread = lib.spreads[request.spread];
  const cards = request.cards.map((dealt, i) => {
    const entry = lib.cards[dealt.card];
    const w = entry.waite;
    const meaning = quote(lib, dealt.reversed ? w.reversed : w.upright);
    return {
      position: i + 1,
      positionName: spread.positions[i].name,
      positionMeaning: quote(lib, spread.positions[i].meaning),
      id: dealt.card,
      name: entry.name,
      orientation: dealt.reversed ? 'reversed' : 'upright',
      picture: quote(lib, w.picture),
      meaning,
      extra: quote(lib, dealt.reversed ? w.extra_reversed : w.extra_upright),
      // A fact about Waite's book, not a missing quote.
      noReversedMeaning: dealt.reversed && !w.reversed,
    };
  });
  return { spread: request.spread, spreadLabel: spread.label, question: request.question, cards, recurrences: recurrences(lib, request.cards) };
}

module.exports = { SPREAD_SIZES, MAX_QUESTION, RequestError, loadLibrary, validateRequest, buildPacket };
