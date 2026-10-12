# Public-domain tarot sources for the reading back end

Research date: 2026-10-12. Compiled by a research agent for Dolores Puckett's
decision on which books the app may quote. Nothing here is loaded into the app yet.

**How it was checked.** "Confirmed" means the page was fetched and read.
Anything seen only in a search snippet, or not read, is marked UNVERIFIED.

**Public-domain test.**

- **US:** a work first published before 1 January 1931 is public domain (PD).
- **EU/UK:** the author must have died more than 70 years ago (before 1956).
- A translation or an edited modern edition has its own copyright question.

## Ranked shortlist: load in this order

| # | Book | Fit | Why |
|---|---|---|---|
| 1 | Waite, *The Pictorial Key to the Tarot* | High | The deck's own book: upright and reversed meanings for all 78 cards, plus the Celtic Cross. Clearest PD status. |
| 2 | Mathers, *The Tarot* (1888) | High | Short upright and reversed meanings for 78 cards, several spreads, Golden Dawn lineage. |
| 3 | Crowley, *Liber LXXVIII* (*The Equinox* I no. 8, 1912) | Medium-high | Dignities, plus house and zodiac spreads in the Book T family. Check how it differs from the Book T data already in `cards/` first. |
| 4 | Thierens, *General Book of the Tarot* (1930) | Medium-high | Lays a reading out as an astrological chart. Uses modern planets (Uranus); quote it as one voice. |
| 5 | Grand Orient (Waite), *A Manual of Cartomancy* (4th ed., 1909) | Medium | Load last, and only after reading its tarot section, which was not verified. |

## The books

### 1. Waite, *The Pictorial Key to the Tarot*

**Edition and text**

- Edition to use: the Wikisource transcription of the 1922 Rider printing ("First Published 1910, Reprinted 1922").
  - Wikisource: https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot
  - The transcription is page-by-page proofread and marked "validated".
  - Wikisource transcriptions carry a CC BY-SA label, so attribute Wikisource when quoting.
- A second copy is on sacred-texts: https://sacred-texts.com/book/the-pictorial-key-to-the-tarot. Its credit line was not read.
- Dates are UNVERIFIED because sources disagree: *The Key to the Tarot* (unillustrated, 1909/1910) versus the *Pictorial Key* (1910/1911). The two texts are believed to be largely the same, but this is unconfirmed.

**Public domain**

- US: yes, published before 1931.
- Life+70: yes. Waite died 1942; the illustrator, Pamela Colman Smith, died 1951.

**Contents** (confirmed at https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot/Part_3)

- Part III §2: divinatory meanings of the Lesser Arcana (the 56 suit cards).
- Part III §3: divinatory meanings of the Greater Arcana (the 22 trumps), each with a "Reversed:" entry.
- §4: additional meanings of the Lesser Arcana.
- §5: recurrence of cards in dealing.
- §6: "The Art of Tarot Divination".
- §7: "An Ancient Celtic Method of Divination" (the Celtic Cross). It names ten positions:
  1. What covers him
  2. What crosses him
  3. What crowns him
  4. What is beneath him
  5. What is behind him
  6. What is before him
  7. Himself
  8. His house
  9. His hopes or fears
  10. What will come
- §8: an alternative method. §9: a 35-card method (heading only, not read).
- Part III also opens with a 42-card operation (from the heading list, not read).

**Trap: the De Laurence copy.** Project Gutenberg #43548 is Waite's text sold by L. W. De Laurence as *The Illustrated Key to the Tarot* ("Copyright, 1918"), without crediting Waite. Never cite it.

### 2. Mathers, *The Tarot* ([1888])

**Text:** sacred-texts: https://sacred-texts.com/book/the-tarot

**Unverified details:** the long subtitle and the publisher.

**Public domain**

- US: yes.
- Life+70: yes. Mathers died 1918 (general knowledge, not fetched).

**Contents**

- Meanings for the 78 cards, with reversed meanings marked "R.". Some entries were read; the 78 were not all counted.
- Methods of divination: a 78-card horseshoe method with heaps, a 21-card method in three rows of seven with a Significator, and a 66-card triangle-and-circle method. No Celtic Cross.

**Matching cards to the app:** Mathers numbers the trumps his own way and names the suits Sceptres and Pentacles. Map his entries to the app by card name, not by number.

### 3. Crowley, *Liber LXXVIII* (*The Equinox* I no. 8, Sept 1912)

- **Text:** sacred-texts: https://sacred-texts.com/oto/lib78.htm
- **Public domain:**
  - US: yes (1912).
  - Life+70: yes. Crowley died 1947.
- **Contents:** the 22 Keys with their attributions; the Aces, courts and 36 decans; "Brief Meaning of Twenty-two Keys"; "Of the Dignities"; and "A Method of Divination by the Tarot" (whole pack with a Significator, laid out by houses, signs and the Tree of Life).
- **Unverified:** whether it is the same text as Book T.
- **Trap:** use only the 1912 text, not Weiser's 1976 *Tarot Divination* reprint.

### 4. Thierens, *General Book of the Tarot* (D. McKay, [1930], introduction by Waite)

- **Text:** sacred-texts: https://sacred-texts.com/book/general-book-of-the-tarot
- **Public domain:**
  - US: yes. It entered PD on 1 January 2026, and sacred-texts says it was also not renewed.
  - Life+70: probably yes. The only death date found (1941) is from a bookshop listing.
- **Contents:** a "Method of Divination" that lays the cards out as the twelve houses of the horoscope, and one chapter per trump tied to a sign or planet.
- **Caution:** it assigns modern planets (for example, the Tower to Uranus). Quote it with the author named.

### 5. Grand Orient (Waite), *A Manual of Cartomancy*

- **Edition:** 4th edition, Rider, 1909.
- **Text:** raw OCR scan only: https://archive.org/details/manualofcartoman00gran. It needs proofreading before quoting.
- **Unverified:**
  - Whether its tarot section ("The Book of the Secret Word and the Higher Way to Fortune") covers all 78 cards and gives reversed meanings.
  - That "Grand Orient" is Waite. This is accepted in a catalogue snippet only.

### Lower fit

| Book | Why lower |
|---|---|
| Papus, *The Tarot of the Bohemians* (A. P. Morton translation) | Mostly symbolic, not divinatory. Use the 1892 Chapman and Hall edition (HathiTrust: https://catalog.hathitrust.org/Record/100770666), not the 1910 revision, which Wellcome labels "In copyright". |
| Foli, *Fortune-Telling by Cards* (1915) | Mostly the 32-card playing pack. Ch. XVIII "The Tarots" and ch. XIX "Etteilla's Method" were not read. |
| Ouspensky, *The Symbolism of the Tarot* (1913) | Trumps only, as essays. Avoid the Tyson-edited and Dover 1976 editions. |
| Etteilla (1783–85) | French only (Wellcome scan: https://wellcomecollection.org/works/ux34pwxe). No PD English translation was found. |

## Do not use

- **Crowley, *The Book of Thoth* (1944).** Still under US copyright.
- **De Laurence, *The Illustrated Key to the Tarot*** (Gutenberg #43548). This is Waite's text without credit.
- **Papus, 1910 revised edition.** Labelled "In copyright" by Wellcome.
- **Modern annotated or translated reprints** (Dover, Weiser, US Games, Tyson). Also modern translations of Wirth, Etteilla and Christian, and Case's later works.

## Licensing flag for Dolores

The sacred-texts files for Mathers and Thierens carry a notice that allows "any non-commercial purpose". The books themselves are PD, but if Aeonic Arts is commercial:

- Do not copy those files wholesale.
- Transcribe from a scan instead, or use a source without that notice, or ask sacred-texts for permission.

This is a risk flag, not legal advice.

## Could not verify

- Dates of *The Key to the Tarot* versus the *Pictorial Key*, and whether their texts match.
- Mathers' long title and publisher.
- Whether *Liber LXXVIII* is the same as Book T.
- The tarot sections of the Grand Orient *Manual*, Foli and Papus (not read).
- Death dates for Morton, Pogossky, Foli and Thierens.
- Changes between the 1892 and 1910 Papus editions.
- A confirmed scan of Case (1920).
- Wikisource's terms for reuse on a commercial site.
