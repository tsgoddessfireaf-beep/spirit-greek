// Checks for the reading library (knowledge/). Run: node --test
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { CARDS, SPREADS, ACES } = require('../deck.js');
const E = require('../engine.js');
const { normalize } = require('../knowledge/text.js');
const { build, json, OUT } = require('../knowledge/tools/build.js');
const K = require('../knowledge/index.js');

const KDIR = path.join(__dirname, '..', 'knowledge');
const lib = K.load();
const sources = Object.fromEntries(lib.sources.map((s) => [s.id, s]));
const waiteFile = path.join(__dirname, '..', sources['waite-pkt'].transcription.file);
const waiteText = normalize(fs.readFileSync(waiteFile, 'utf8'));

test('library files match a fresh build from the saved source (no hand edits)', () => {
  const built = build();
  for (const [key, file] of Object.entries(OUT)) {
    assert.equal(fs.readFileSync(path.join(KDIR, file), 'utf8'), json(built[key]), `${file} is stale: run node knowledge/tools/build.js`);
  }
});

test('saved source page is the one recorded in the source ledger', () => {
  const sha = crypto.createHash('sha256').update(fs.readFileSync(waiteFile)).digest('hex');
  assert.equal(sha, sources['waite-pkt'].transcription.file_sha256);
});

test('every quote appears word for word in its source', () => {
  const all = K.quotes(lib);
  assert.ok(all.length > 300);
  for (const q of all) {
    assert.ok(sources[q.source], `unknown source ${q.source}`);
    assert.ok(q.text.length > 0, `${q.id} is empty`);
    assert.ok(waiteText.includes(q.text), `${q.id} is not word for word in the source`);
  }
  assert.equal(new Set(all.map((q) => q.id)).size, all.length, 'quote ids are unique');
});

test('all 78 cards have Waite meanings, matched to the app deck', () => {
  assert.equal(lib.cards.length, 78);
  lib.cards.forEach((c, i) => {
    assert.equal(c.id, CARDS[i].id);
    assert.equal(c.name, CARDS[i].name);
    assert.ok(c.waite.upright, `${c.name}: no upright meaning`);
    // Waite gives no reversed meaning for the Two of Cups; every other card has one.
    if (c.name !== 'Two of Cups') assert.ok(c.waite.reversed, `${c.name}: no reversed meaning`);
    if (CARDS[i].arcana === 'minor') {
      assert.ok(c.waite.picture, `${c.name}: no picture description`);
      assert.ok(c.waite.extra_upright, `${c.name}: no additional meaning`);
    }
  });
  // Spot checks against the book.
  assert.match(lib.cards[1].waite.upright.text, /^Skill, diplomacy, address, subtlety/);
  assert.equal(lib.cards[8].waite.upright.text, 'Power, energy, action, courage, magnanimity; also complete success and honours.');
  assert.equal(lib.cards[67].waite.reversed.text, 'Suspense, delay, opposition.');
});

test('room for Dolores\'s wording on every card, empty in this public repository', () => {
  for (const c of lib.cards) {
    assert.deepEqual(c.owner, { upright: null, reversed: null, notes: null }, c.name);
  }
});

test('nothing is verified until Dolores approves it', () => {
  const approved = JSON.parse(fs.readFileSync(path.join(KDIR, 'verified.json'), 'utf8')).verified;
  const ids = new Set(K.quotes(lib).map((q) => q.id));
  for (const id of Object.keys(approved)) assert.ok(ids.has(id), `verified.json names unknown quote ${id}`);
  assert.equal(K.verifiedQuotes(lib).length, Object.keys(approved).length);
  for (const q of K.quotes(lib)) assert.ok(['draft', 'verified'].includes(q.status));
});

test('Celtic Cross: Waite\'s meanings sit on the app\'s spots by name', () => {
  const celtic = lib.spreads.celtic;
  assert.deepEqual(celtic.positions.map((p) => p.name), SPREADS.celtic.positions);
  assert.deepEqual([...celtic.positions.map((p) => p.waite_number)].sort((a, b) => a - b), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  // The six cross positions: the app's name and Waite's spoken words agree.
  for (const p of celtic.positions.slice(0, 6)) {
    const word = p.name.split(' ')[0].toLowerCase();
    assert.ok(p.waite_words.toLowerCase().includes(word), `${p.name} vs "${p.waite_words}"`);
  }
  assert.equal(celtic.positions[2].waite_number, 4);   // app spot 3, below = Waite 4, beneath
  assert.equal(celtic.positions[4].waite_number, 3);   // app spot 5, above = Waite 3, crowns
  assert.ok(celtic.rules.length >= 6);
});

test('Yes / No rulebook gives the same answers as the app', () => {
  const t = lib.spreads.yesno.answers;
  const blank = CARDS.find((c) => !ACES.includes(c.id)).id;
  const pile = (v) => [{ card: v === 'blank' ? blank : ACES[0], reversed: v === 'down' }];
  let combos = 0;
  for (let up = 0; up <= 3; up++) {
    for (let down = 0; up + down <= 3; down++) {
      combos++;
      const votes = [...Array(up).fill('up'), ...Array(down).fill('down'), ...Array(3 - up - down).fill('blank')];
      const got = E.scoreYesNo(votes.map(pile), ACES);
      const row = t.find((r) => r.up === up && r.down === down);
      assert.ok(row, `no rulebook row for ${up} up / ${down} down`);
      assert.equal(row.key, got.key);
      assert.equal(row.answer, got.answer);
    }
  }
  assert.equal(t.length, combos);
});

test('recurrence rules cover 2, 3 and 4 of every rank, upright and reversed', () => {
  const items = lib.rules.recurrence.items;
  assert.equal(items.length, 14 * 3 * 2);
  const keys = new Set(items.map((i) => `${i.orientation}:${i.count}:${i.rank}`));
  assert.equal(keys.size, items.length);
});

test('spreads with no source yet say so instead of inventing meanings', () => {
  for (const key of ['one', 'three']) {
    const s = lib.spreads[key];
    assert.ok(s.source_note);
    for (const p of s.positions) assert.equal(p.meaning, null);
  }
});

// ---- The phone page reads knowledge/approved.json: approved quotes only ----
const { approvedFile } = require('../knowledge/tools/build.js');

test('phone page file holds no draft text (verified.json is the only way in)', () => {
  const approvedJson = JSON.parse(fs.readFileSync(path.join(KDIR, 'approved.json'), 'utf8'));
  const approvedIds = new Set(Object.keys(JSON.parse(fs.readFileSync(path.join(KDIR, 'verified.json'), 'utf8')).verified));
  const shown = Object.values(approvedJson.cards).flatMap((c) => [c.upright, c.reversed].filter(Boolean));
  for (const text of shown) {
    const q = K.quotes(lib).find((x) => x.text === text);
    assert.ok(q, 'shown text is not a known quote');
    assert.ok(approvedIds.has(q.id), `${q.id} is shown but not approved`);
  }
});

test('approved file includes exactly the quotes listed as approved', () => {
  const built = build();
  const upId = built.cards[0].waite.upright.id;
  const f = approvedFile(built, new Set([upId]));
  assert.equal(f.cards[0].upright, built.cards[0].waite.upright.text);
  assert.equal(f.cards[0].reversed, undefined, 'an unapproved reversed meaning must not appear');
  // Card 0 (approved upright) and card 37 (Two of Cups: no reversed in the source).
  assert.deepEqual(Object.keys(f.cards), ['0', '37']);
});

test('Two of Cups is marked as having no reversed meaning in the source', () => {
  const approvedJson = JSON.parse(fs.readFileSync(path.join(KDIR, 'approved.json'), 'utf8'));
  assert.equal(approvedJson.cards[37].noReversed, true);
});

test('the page loads only approved.json, never the draft library', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  assert.match(html, /knowledge\/approved\.json/);
  for (const draft of ['cards.json', 'spreads.json', 'rules.json', 'verified.json', 'sources.json']) {
    assert.ok(!html.includes(draft), `index.html must not load ${draft}`);
  }
});
