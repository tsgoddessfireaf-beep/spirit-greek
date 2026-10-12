// Runs before every deploy. Copies the reading library into functions/knowledge so the
// server can read it. The copy is never committed (see functions/.gitignore).
'use strict';
const fs = require('fs');
const path = require('path');

const FROM = path.join(__dirname, '..', '..', 'knowledge');
const TO = path.join(__dirname, '..', 'knowledge');
const FILES = ['cards.json', 'spreads.json', 'rules.json', 'verified.json'];

fs.mkdirSync(TO, { recursive: true });
for (const f of FILES) fs.copyFileSync(path.join(FROM, f), path.join(TO, f));
console.log(`Copied ${FILES.length} library files to functions/knowledge`);
