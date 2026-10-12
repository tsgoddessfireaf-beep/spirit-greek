#!/usr/bin/env node
// Builds the reading library from the saved source pages.
//
//   node knowledge/tools/build.js          writes knowledge/cards.json, spreads.json, rules.json
//   node knowledge/tools/build.js --check  only checks that those files are up to date
//
// Every quote is cut word for word from the saved Wikisource page, after the
// formatting-only clean-up in knowledge/text.js. Nothing is typed in by hand
// except the parts that have no book source yet (One card, Three cards) and
// Dolores's own Yes / No method, which are marked as such.
// Whether a quote is approved is NOT stored here: see knowledge/verified.json.
'use strict';

const fs = require('fs');
const path = require('path');
const { normalize } = require('../text.js');
const { CARDS, SPREADS } = require('../../deck.js');

const ROOT = path.join(__dirname, '..');
const WAITE_FILE = path.join(ROOT, 'sources', 'waite-pkt-part3.wikisource.md');
const SRC = 'waite-pkt';

const SUITS = { WANDS: 'Wands', CUPS: 'Cups', SWORDS: 'Swords', PENTACLES: 'Coins' };
const RANKS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
  'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King'];
// Waite's names for two trumps differ from the app's (Waite 1910 card titles).
const TRUMP_ALIASES = { Fortitude: 'Strength', 'The Last Judgment': 'Judgement' };

const cardByName = new Map(CARDS.map((c) => [c.name, c]));
function minorId(suitWord, rank) {
  const name = `${rank} of ${SUITS[suitWord.toUpperCase()]}`;
  const card = cardByName.get(name);
  if (!card) throw new Error(`No card named ${name}`);
  return card.id;
}

// Split the page into its numbered sections (§ 1 … § 9).
function sections(md) {
  const out = {};
  const parts = md.split(/^§ (\d)/m);
  for (let i = 1; i < parts.length; i += 2) out[parts[i]] = parts[i + 1];
  return out;
}

// "<picture> Divinatory Meanings: X Reversed: Y" → { before, upright, reversed }.
// The source sometimes prints "Reversed;" or "Reversed :"; all count as the label.
// Waite gives no reversed meaning for a few cards: reversed is then null.
const DIVINATORY = 'Divinatory Meanings:';
function splitMeaning(text, label) {
  const d = text.indexOf(DIVINATORY);
  if (label && d < 0) throw new Error(`${label}: no "${DIVINATORY}"`);
  const r = text.search(/Reversed\s*[:;]/);
  const upStart = d < 0 ? 0 : d + DIVINATORY.length;
  return {
    before: d < 0 ? '' : text.slice(0, d).trim(),
    upright: text.slice(upStart, r < 0 ? undefined : r).trim(),
    reversed: r < 0 ? null : text.slice(r).replace(/^Reversed\s*[:;]\s*/, '').trim(),
  };
}

function quote(id, where, text) {
  if (!text) return null;
  return { id, source: SRC, where, text };
}

// § 2: each suit card, with Waite's description of the picture and its meanings.
function lesserArcana(sec) {
  const out = {};
  let suit = null;
  let rank = null;
  let buf = [];
  const flush = () => {
    if (!suit || !rank) return;
    const text = normalize(buf.join(' '));
    const id = minorId(suit, rank);
    const parts = splitMeaning(text, `${rank} of ${suit}`);
    out[id] = {
      picture: quote(`${SRC}:card:${id}:picture`, 'Part III §2', parts.before),
      upright: quote(`${SRC}:card:${id}:upright`, 'Part III §2', parts.upright),
      reversed: quote(`${SRC}:card:${id}:reversed`, 'Part III §2', parts.reversed),
    };
    rank = null;
    buf = [];
  };
  for (const raw of sec.split('\n')) {
    const line = normalize(raw);
    if (!line || line.startsWith('[![')) continue;
    if (line.startsWith('Such are the intimations')) break;   // closing remarks of § 2
    const suitHead = line.match(/^(?:THE SUIT OF )?(WANDS|CUPS|SWORDS|PENTACLES)$/);
    if (suitHead) { flush(); suit = suitHead[1]; continue; }
    if (RANKS.includes(line)) { flush(); rank = line; continue; }
    if (rank) buf.push(line);
  }
  flush();
  return out;
}

// § 3: the trumps, one line each: "1. The Magician.—… Reversed: …"
function greaterArcana(sec) {
  const out = {};
  for (const raw of sec.split('\n')) {
    const line = normalize(raw);
    const m = line.match(/^(?:\d+\.|Zero\.)\s+(.+?)\.—(.*)$/);
    if (!m) continue;
    const name = TRUMP_ALIASES[m[1]] || m[1];
    const card = cardByName.get(name);
    if (!card || card.arcana !== 'major') throw new Error(`Unknown trump: ${m[1]}`);
    const parts = splitMeaning(m[2]);
    out[card.id] = {
      upright: quote(`${SRC}:card:${card.id}:upright`, 'Part III §3', parts.upright.replace(/,$/, '')),
      reversed: quote(`${SRC}:card:${card.id}:reversed`, 'Part III §3', parts.reversed),
    };
  }
  return out;
}

// § 4: "Some additional meanings of the Lesser Arcana".
function additional(sec) {
  const out = {};
  let suit = null;
  for (const raw of sec.split('\n')) {
    let line = normalize(raw);
    const s = line.match(/^(Wands|Cups|Swords|Pentacles)\.\s*(.*)$/);
    if (s) { suit = s[1]; line = s[2]; }
    const m = line.match(/^(Ace|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Page|Knight|Queen|King)\.—(.*)$/);
    if (!m || !suit) continue;
    const id = minorId(suit, m[1]);
    const parts = splitMeaning(m[2]);
    out[id] = {
      upright: quote(`${SRC}:card:${id}:extra-upright`, 'Part III §4', parts.upright),
      reversed: quote(`${SRC}:card:${id}:extra-reversed`, 'Part III §4', parts.reversed),
    };
  }
  return out;
}

// § 5: what it means when 2, 3 or 4 cards of one rank fall in a reading.
const PLURALS = ['Kings', 'Queens', 'Knights', 'Pages', 'Tens', 'Nines', 'Eights',
  'Sevens', 'Sixes', 'Fives', 'Fours', 'Threes', 'Twos', 'Aces'];
function recurrence(sec) {
  const text = normalize(sec);
  const [natural, reversed] = text.split('Reversed');
  const parse = (block, orientation) => {
    const items = [];
    const re = new RegExp(`([234])\\.?\\s+(${PLURALS.join('|')})\\s*=?\\s*(.*?)\\s*(?=[;.]?\\s*[234]\\.?\\s+(?:${PLURALS.join('|')})\\b|[;.]?\\s*§|$)`, 'g');
    for (const m of block.matchAll(re)) {
      const meaning = m[3].replace(/[;.]$/, '').trim();
      if (!meaning) continue;
      items.push({
        count: Number(m[1]), rank: RANKS[13 - PLURALS.indexOf(m[2])] || m[2], orientation,
        meaning: quote(`${SRC}:recurrence:${orientation}:${m[1]}-${m[2].toLowerCase()}`, 'Part III §5', meaning),
      });
    }
    return items;
  };
  return [...parse(natural, 'upright'), ...parse(reversed, 'reversed')];
}

// Cut a passage from start phrase to end phrase, inclusive.
function between(text, start, end, label) {
  const a = text.indexOf(start);
  const b = text.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`Passage not found: ${label}`);
  return text.slice(a, b + end.length);
}

// § 7: Waite's Celtic Cross. Each position is matched to the app's spot by NAME.
// The app lays the cards in Dolores's order (3 below, 4 left, 5 above), which
// differs from Waite's numbering (3 crowns, 4 beneath, 5 behind).
const CELTIC = [
  { app: 0, waite: 1, said: 'This covers him.', start: 'This card gives the influence', end: 'in which the other currents work.' },
  { app: 1, waite: 2, said: 'This crosses him.', start: 'It shews the nature of the obstacles', end: 'in the particular connexion.' },
  { app: 2, waite: 4, said: 'This is beneath him.', start: 'It shews the foundation or basis', end: 'has made his own.' },
  { app: 3, waite: 5, said: 'This is behind him.', start: 'It gives the influence that is just passed', end: 'is now passing away.' },
  { app: 4, waite: 3, said: 'This crowns him.', start: "It represents (a) the Querent's aim", end: 'not yet been made actual.' },
  { app: 5, waite: 6, said: 'This is before him.', start: 'It shews the influence that is coming into action', end: 'in the near future.' },
  { app: 6, waite: 7, said: null, start: 'signifies himself', end: 'attitude in the circumstances.' },
  { app: 7, waite: 8, said: null, start: 'The Eighth Card signifies his house', end: 'and so forth.' },
  { app: 8, waite: 9, said: null, start: 'The Ninth Card gives his hopes or fears', end: 'in the matter.' },
  { app: 9, waite: 10, said: null, start: 'The Tenth is what will come', end: 'turned up in the divination.' },
];
const CELTIC_RULES = [
  { id: 'significator', start: 'The Diviner first selects a card', end: 'any female of less age.' },
  { id: 'significator-by-colouring', start: 'The four Court Cards in Wands', end: 'rather than to Wands.' },
  { id: 'significator-by-matter', start: 'If it is more convenient', end: 'to each of the parties concerned.' },
  { id: 'shuffle-and-cut', start: 'Having selected the Significator', end: 'faces of the cards downwards.' },
  { id: 'facing', start: 'N.B.—If the Significator', end: 'as facing.' },
  { id: 'tenth-card-focus', start: 'It is on this card that the Diviner', end: 'a Trump Major.' },
  { id: 'repeat-if-dubious', start: 'The operation is now completed', end: 'may be obtained.' },
  { id: 'tenth-card-court', start: 'If in any divination the Tenth Card', end: 'to what issue he will bring it.' },
];
function celticCross(sec) {
  const text = normalize(sec);
  const names = SPREADS.celtic.positions;
  const positions = CELTIC.map((p) => ({
    index: p.app,
    name: names[p.app],
    waite_number: p.waite,
    waite_words: p.said,
    meaning: quote(`${SRC}:celtic:position-${p.waite}`, 'Part III §7',
      between(text, p.start, p.end, `Celtic position ${p.waite}`)),
  }));
  const rules = CELTIC_RULES.map((r) => ({
    id: r.id,
    text: quote(`${SRC}:celtic:${r.id}`, 'Part III §7', between(text, r.start, r.end, r.id)),
  }));
  return { positions, rules };
}

// Places where the Wikisource transcription looks wrong. The text is kept exactly
// as transcribed; the note tells the reviewer what to check against the page scan.
const TRANSCRIPTION_NOTES = {
  'waite-pkt:card:2:upright': 'Reads "if female silence"; the printed book probably has a semicolon ("if female; silence"). Check the scan.',
  'waite-pkt:card:17:upright': 'The source prints a comma before "Reversed:"; the comma is left off the end of this quote.',
  'waite-pkt:card:20:upright': 'Reads "total loss though lawsuit"; probably "through". Check the scan.',
  'waite-pkt:card:38:extra-reversed': 'Reads "cure. end of the business"; the full stop may be a comma. Check the scan.',
  'waite-pkt:card:50:reversed': '"conceрtion" is typed with a Cyrillic letter р in place of the Latin p ("conception"). Fix in the transcription before verifying.',
  'waite-pkt:card:67:reversed': 'The source prints "Reversed;" with a semicolon.',
  'waite-pkt:celtic:repeat-if-dubious': 'Reads "What will come me"; check the scan.',
};
function addNotes(value) {
  if (Array.isArray(value)) { value.forEach(addNotes); return; }
  if (!value || typeof value !== 'object') return;
  if (value.id && TRANSCRIPTION_NOTES[value.id]) value.note = TRANSCRIPTION_NOTES[value.id];
  Object.values(value).forEach(addNotes);
}

function build() {
  const md = fs.readFileSync(WAITE_FILE, 'utf8');
  const sec = sections(md);
  const lesser = lesserArcana(sec[2]);
  const greater = greaterArcana(sec[3]);
  const extra = additional(sec[4]);

  const cards = CARDS.map((c) => {
    const main = c.arcana === 'major' ? greater[c.id] : lesser[c.id];
    if (!main) throw new Error(`No Waite entry for ${c.name}`);
    return {
      id: c.id,
      name: c.name,
      waite: {
        picture: main.picture || null,
        upright: main.upright,
        reversed: main.reversed,
        extra_upright: extra[c.id] ? extra[c.id].upright : null,
        extra_reversed: extra[c.id] ? extra[c.id].reversed : null,
      },
      // Dolores's own wording. Always empty in this public repository: her
      // wording will live only on the private server, filled in later.
      owner: { upright: null, reversed: null, notes: null },
    };
  });

  const celtic = celticCross(sec[7]);
  const spreads = {
    one: {
      label: SPREADS.one.label,
      positions: SPREADS.one.positions.map((name, index) => ({ index, name, meaning: null })),
      rules: [],
      source_note: 'No public-domain source chosen yet for a one-card draw.',
    },
    three: {
      label: SPREADS.three.label,
      positions: SPREADS.three.positions.map((name, index) => ({ index, name, meaning: null })),
      rules: [],
      source_note: 'Waite gives no three-card spread. Position meanings wait for a source.',
    },
    celtic: {
      label: SPREADS.celtic.label,
      source: SRC,
      layout_note: "Cards are laid in Dolores's order (1 center, 2 across, 3 below, 4 left, 5 above, 6 right, 7-10 bottom to top). Waite's meanings are matched by position name; waite_number is Waite's own numbering.",
      positions: celtic.positions,
      rules: celtic.rules,
    },
    yesno: {
      label: SPREADS.yesno.label,
      source: 'owner',
      source_note: "Dolores Puckett's method (issue #6; approved and merged in PR #7). The app's engine.js scoreYesNo must give the same answers; a test checks this.",
      piles: SPREADS.yesno.piles.count,
      pile_stops: 'Each pile stops at an Ace or after 13 cards. Reversed cards are always on.',
      votes: { up: 'upright Ace = yes', down: 'reversed Ace = no', blank: 'no Ace' },
      answers: [
        { up: 3, down: 0, key: 'yes', answer: 'Yes' },
        { up: 2, down: 0, key: 'likelyYes', answer: 'Likely yes' },
        { up: 2, down: 1, key: 'likelyYes', answer: 'Likely yes' },
        { up: 1, down: 0, key: 'maybeYes', answer: 'Maybe yes' },
        { up: 1, down: 1, key: 'unclear', answer: 'No clear answer' },
        { up: 0, down: 0, key: 'unclear', answer: 'No clear answer' },
        { up: 0, down: 1, key: 'maybeNo', answer: 'Maybe no' },
        { up: 1, down: 2, key: 'likelyNo', answer: 'Likely no' },
        { up: 0, down: 2, key: 'likelyNo', answer: 'Likely no' },
        { up: 0, down: 3, key: 'no', answer: 'No' },
      ],
      unclear_note: 'No clear answer: read the other cards as a story.',
    },
  };

  const rules = {
    recurrence: {
      applies_to: 'every spread',
      source: SRC,
      where: 'Part III §5',
      items: recurrence(sec[5]),
    },
  };

  const built = { cards, spreads, rules };
  addNotes(built);
  const verified = new Set(Object.keys(JSON.parse(fs.readFileSync(path.join(ROOT, 'verified.json'), 'utf8')).verified));
  built.approved = approvedFile(built, verified);
  return built;
}

// The file the phone page reads. It holds ONLY quotes listed in verified.json, so
// draft text never reaches a reader. "noReversed" is a fact about the source (Waite
// gives no reversed meaning), not a quote, so it needs no approval.
function approvedFile(built, verified) {
  const cards = {};
  for (const c of built.cards) {
    const out = {};
    const up = c.waite.upright;
    const rev = c.waite.reversed;
    if (up && verified.has(up.id)) out.upright = up.text;
    if (rev && verified.has(rev.id)) out.reversed = rev.text;
    if (!rev) out.noReversed = true;
    if (Object.keys(out).length) cards[c.id] = out;
  }
  return {
    about: 'Approved quotes only. Written by knowledge/tools/build.js from verified.json. Do not edit by hand.',
    cards,
  };
}

const json = (v) => `${JSON.stringify(v, null, 1)}\n`;
const OUT = { cards: 'cards.json', spreads: 'spreads.json', rules: 'rules.json', approved: 'approved.json' };

if (require.main === module) {
  const built = build();
  const check = process.argv.includes('--check');
  let stale = 0;
  for (const [key, file] of Object.entries(OUT)) {
    const target = path.join(ROOT, file);
    const want = json(built[key]);
    if (check) {
      const have = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : '';
      if (have !== want) { stale++; console.error(`${file} is out of date`); }
    } else {
      fs.writeFileSync(target, want);
      console.log(`wrote knowledge/${file}`);
    }
  }
  process.exit(stale ? 1 : 0);
}

module.exports = { build, json, OUT, approvedFile };
