// One rule for turning a saved source page into plain text. The build script and
// the tests both use it, so "word for word" always means the same thing.
// It changes only formatting, never words or punctuation:
//   - zero-width spaces (U+200B, left by Wikisource page breaks) are removed
//   - soft hyphens (U+00AD, invisible line-break hints) are removed
//   - Markdown marks for italics and bold (_ and **) are removed
//   - escaped dots ("1\.") lose their backslash
//   - a space just inside an opening bracket ("( a)") is removed
//   - runs of spaces and line breaks become one space
'use strict';

function normalize(text) {
  return text
    .replace(/[​­]/g, '')
    .replace(/\*\*/g, '')
    .replace(/_/g, '')
    .replace(/\\\./g, '.')
    .replace(/\(\s+/g, '(')
    .replace(/\s+/g, ' ')
    .trim();
}

module.exports = { normalize };
