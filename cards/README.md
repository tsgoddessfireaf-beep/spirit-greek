# Cards: images and Golden Dawn attributions

The app shows the Aeonic Arts edition (`img/cards/`, made from `aeonic/`). The other
files here are source material and data.

## `aeonic/`: the Aeonic Arts edition (78 cards)

The 1909 cards below, recolored for Aeonic Arts:

- Palette: deep teal ink, cream paper, amber-gold and teal from the card back.
- Cups and coins silver; swords gold (Justice and the Wheel of Fortune too).
- Every pentagram coin replaced by a silver coin with thin teal circles and a copper
  hexagon and Y. The Three of Coins' carved pentagrams are carved hexagons with a Y.
  The Devil's pentagram is left as Smith drew it.
- The fourth suit is **Coins**: "PENTACLES" re-lettered as "COINS" on the Ace, Page,
  Knight, Queen and King, from Smith's own letters.
- Deep copper lettering (RGB 150, 80, 40: dark enough to read on cream); teal
  outline around each picture.

`aeonic-contact-sheet.jpg` shows all 78. `img/cards/NN.jpg` are 440-pixel-wide copies
for the app (NN = card id).

`aeonic-tools/` rebuilds the edition: `aeonic.py` is the program and `marks.json` holds
the hand-placed marks for every cup, coin and sword:

```
python3 -I cards/aeonic-tools/aeonic.py cards/aeonic-tools/marks.json cards/rws1909 <out-dir> <card names…>
```

Known imperfections: one sword tip in the Eight of Swords stays blue (it sits in water
of the same colour); a few thin white highlight lines on the Seven of Swords stay white;
the re-lettered "COINS" letters come from several cards, so ink weight differs slightly.

## `rws1909/`: the 78 card images

Scans of an original 1909 "Roses & Lilies" first printing of the Rider–Waite–Smith
deck (art by Pamela Colman Smith; scanned by Saskia Jansen), from Wikimedia Commons.
Public domain. File names start with the card `id` from `deck.js`
(`00-the-fool.jpg` … `77-king-of-pentacles.jpg`). `rws1909-contact-sheet.jpg`
shows all 78 at once.

`rws1909/sources.json` records, for every image, its Commons page, download
address, size and SHA-256 fingerprint, and which version it is:

- **original** (25 cards: the 22 Majors and Ace–Three of Cups): the scan exactly
  as uploaded, about 830 × 1430 pixels.
- **wikimedia-thumbnail-960px** (53 cards): Wikimedia's own resized copy, 960
  pixels wide. Wikimedia blocked further full-size downloads (rate limit), so
  these came from its copies instead. They are slightly enlarged from the
  scan; no detail is added or lost that shows on a phone. They can be swapped
  for originals later.

## `golden-dawn-book-t.json`

The astrology the Hermetic Order of the Golden Dawn (the Rosicrucian order that
Waite and Pamela Colman Smith belonged to) gave each of the 78 cards, taken from
**Book T** (Mathers and Felkin, c. 1888; printed openly in *The Equinox*, 1912;
public domain). Card `id` numbers match `deck.js`.

| Cards | What Book T gives them |
|---|---|
| 22 Major Arcana | A Hebrew letter and one planet, sign or element (for example The Magician: Beth, Mercury) |
| Twos to Tens (36 cards) | One decan: a 10° third of a sign and its planetary ruler (for example Two of Wands: Mars in 0°–10° Aries) |
| Knights, Queens, Kings | A span of the zodiac from 20° of one sign to 20° of the next |
| Pages (Book T "Princesses") | A quarter of the sky around the north pole of the ecliptic, above a fixed sign |
| Aces | The root of their element, placed at the pole; no degrees |

Decan rulers follow the Chaldean order (Saturn, Jupiter, Mars, Sun, Venus, Mercury,
Moon). Book T starts the count at Saturn in the first decan of Leo, and gives Mars
two decans in a row (last of Pisces, first of Aries). The build script checks
every decan against that order.

**Court names.** Book T's own table names the cards the Waite way: its Knight is
"King of the Spirits" (mounted), its King is "Prince of the Chariot", its Knave is
the Princess. So Waite's Knight, Queen, King and Page map one-to-one. (Crowley's
Thoth deck renames these; that mapping is different and not used here.)

**Transcription repairs.** Source: the Mathers–Felkin transcription at
<https://benebellwen.com/wp-content/uploads/2013/02/mathers-and-felkin-golden-dawn-book-t-the-tarot-1888.pdf>.
Its PDF tables split or garble a few entries; these were rejoined:
The Fool's title (Greek *Aither* = Aether), The Lovers and The Moon titles (split
across pages), The Wheel's title (merged with its card name), and "Koph" for The
Wheel, written here as Kaph (כ).
