// Reads the reading library and marks every quote "verified" or "draft".
// The future server uses this; only verified quotes may reach a reader.
'use strict';

const fs = require('fs');
const path = require('path');

const read = (file) => JSON.parse(fs.readFileSync(path.join(__dirname, file), 'utf8'));

// Every quote object in the library: anything with an id, a source and text.
function quotes(value, out = []) {
  if (Array.isArray(value)) value.forEach((v) => quotes(v, out));
  else if (value && typeof value === 'object') {
    if (value.id && value.source && typeof value.text === 'string') out.push(value);
    Object.values(value).forEach((v) => quotes(v, out));
  }
  return out;
}

function load() {
  const lib = {
    cards: read('cards.json'),
    spreads: read('spreads.json'),
    rules: read('rules.json'),
    sources: read('sources.json'),
  };
  const approved = read('verified.json').verified;
  for (const q of quotes(lib)) q.status = approved[q.id] ? 'verified' : 'draft';
  return lib;
}

// Only the quotes Dolores has approved.
function verifiedQuotes(lib) {
  return quotes(lib).filter((q) => q.status === 'verified');
}

module.exports = { load, quotes, verifiedQuotes };
