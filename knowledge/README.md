# Reading library

This folder is the app's library of card meanings and spread rules. A future
server will read it to write readings. The phone page does not use it yet.

## What is here

| File | What it holds |
|---|---|
| `cards.json` | All 78 cards. For each card: Waite's description of the picture (suit cards only), its upright and reversed meanings, and Waite's "additional meanings". Each card also has an empty `owner` slot for Dolores's own wording. |
| `spreads.json` | The four spreads: what each position means, plus the rules for reading the spread. |
| `rules.json` | Rules that apply to every spread. Today this holds Waite's meanings for 2, 3 or 4 cards of one rank in a reading (for example, "3 Kings = consultation"). |
| `sources.json` | The source ledger: each book, its edition, why it is public domain, and where the saved copy came from. |
| `verified.json` | The quotes Dolores has approved. Empty until she approves some. |
| `approved.json` | Generated from `verified.json`. Holds only approved quotes, and is the only library file the phone page reads. Never edit by hand. |
| `sources/` | The saved source page, exactly as it was downloaded. |
| `tools/build.js` | The program that cuts the quotes out of the saved page. |
| `text.js` | The one formatting clean-up rule, used by both the program and the tests. |
| `index.js` | Loads the library and marks each quote "verified" or "draft". |

## Rules the library follows

1. **Word for word.** Every meaning is cut from the saved copy of Waite's *Pictorial Key to the Tarot*. Nothing is typed in by hand.
   - The only clean-up is formatting: invisible characters, italic marks and extra spaces. The full list is in `text.js`.
   - A test checks that every quote appears in the source exactly.
2. **Drafts stay hidden.** Every quote is a draft until Dolores approves it in `verified.json`. Only approved quotes may reach a reader.
3. **No invented meanings.** One card and Three cards have no public-domain source yet, so their position meanings are empty. The library says so instead of making something up.
4. **Matched by name, not number.** The Celtic Cross uses Dolores's laying order (3 below, 4 left, 5 above). Waite numbers the cards differently (3 crowns, 4 beneath, 5 behind). Each of Waite's meanings is attached to the spot with the same name, and `waite_number` records Waite's own number.
5. **Dolores's own wording stays private.** The `owner` slot on every card is always empty in this public repository. Her wording will live only on the private server, added later.
6. **Typos in the source are flagged, not fixed.** Where the Wikisource copy looks wrong, the quote carries a `note` saying what to check against the page scan. For example, the Ace of Swords has a Russian letter р typed in place of an English p.

## Changing the library

- **To approve a quote,** add its `id` to `verified.json`, with who approved it and the date.
- **To rebuild after changing the program or adding a source,** run:

  ```
  node knowledge/tools/build.js
  ```

- **To check everything,** run:

  ```
  node --test
  ```

  One test fails if anyone edits `cards.json`, `spreads.json` or `rules.json` by hand. Those three files must always come from the build program.
