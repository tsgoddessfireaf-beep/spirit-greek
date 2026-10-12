// Checks Claude's reply before any reader sees it. A reply that fails is retried once,
// then replaced by Waite's plain words.
'use strict';

const MAX_TEXT = 1500;

// Reads the JSON from a reply, allowing stray text around it.
function parseReply(text) {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
}

// Names that are safe to search for in prose. One-word major cards (Strength, Justice,
// Death, Temperance, Judgement) are ordinary words, so only full names are checked.
function checkableNames(allCards) {
  return allCards.map((c) => c.name).filter((n) => n.includes(' '));
}

function escape(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function checkReading(reply, packet, allCards) {
  const problems = [];
  if (!reply || typeof reply !== 'object') return ['The reply was not valid JSON in the required shape.'];
  if (typeof reply.intro !== 'string' || !reply.intro.trim()) problems.push('Missing intro.');
  if (typeof reply.summary !== 'string' || !reply.summary.trim()) problems.push('Missing summary.');
  if (!Array.isArray(reply.cards) || reply.cards.length !== packet.cards.length) {
    problems.push(`Expected ${packet.cards.length} cards, in position order.`);
    return problems;
  }
  packet.cards.forEach((want, i) => {
    const got = reply.cards[i] || {};
    if (got.position !== want.position) problems.push(`Entry ${i + 1} must be position ${want.position}.`);
    if (got.card !== want.name) problems.push(`Position ${want.position} must be ${want.name}.`);
    if (got.orientation !== want.orientation) problems.push(`${want.name} is ${want.orientation}, not ${got.orientation}.`);
    if (typeof got.text !== 'string' || !got.text.trim()) problems.push(`Missing text for ${want.name}.`);
  });
  const prose = [reply.intro, reply.summary, ...reply.cards.map((c) => (c && c.text) || '')].filter((t) => typeof t === 'string');
  if (prose.some((t) => t.length > MAX_TEXT)) problems.push(`Keep each part under ${MAX_TEXT} characters.`);
  const dealt = new Set(packet.cards.map((c) => c.name));
  for (const name of checkableNames(allCards)) {
    if (dealt.has(name)) continue;
    if (prose.some((t) => new RegExp(`\\b${escape(name)}\\b`, 'i').test(t))) problems.push(`${name} was not dealt. Do not mention it.`);
  }
  return problems;
}

module.exports = { parseReply, checkReading };
