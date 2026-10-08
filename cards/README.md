# Cards: images and Golden Dawn attributions

Data only. The app does not use these files yet.

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
