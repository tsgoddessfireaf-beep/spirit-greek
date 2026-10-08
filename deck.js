// The 78 cards of a standard tarot deck: names and suits only.
// No meanings, no images. Names follow the public-domain Waite (1910) deck.
(function (root) {
  'use strict';

  const MAJORS = [
    'The Fool', 'The Magician', 'The High Priestess', 'The Empress', 'The Emperor',
    'The Hierophant', 'The Lovers', 'The Chariot', 'Strength', 'The Hermit',
    'Wheel of Fortune', 'Justice', 'The Hanged Man', 'Death', 'Temperance',
    'The Devil', 'The Tower', 'The Star', 'The Moon', 'The Sun', 'Judgement', 'The World',
  ];
  const NUMERALS = [
    '0', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX', 'XXI',
  ];
  const SUITS = ['Wands', 'Cups', 'Swords', 'Pentacles'];
  const RANKS = [
    'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven',
    'Eight', 'Nine', 'Ten', 'Page', 'Knight', 'Queen', 'King',
  ];

  const CARDS = [];
  MAJORS.forEach((name, i) => {
    CARDS.push({ id: CARDS.length, name, arcana: 'major', suit: null, numeral: NUMERALS[i] });
  });
  SUITS.forEach((suit) => {
    RANKS.forEach((rank) => {
      CARDS.push({ id: CARDS.length, name: `${rank} of ${suit}`, arcana: 'minor', suit, numeral: null });
    });
  });

  // Spread positions. Celtic Cross uses Dolores's laying order:
  // 1 center, 2 across 1, 3 below, 4 left, 5 above, 6 right, staff 7-10 bottom to top.
  // Each spot keeps its traditional (Waite 1910) name.
  const SPREADS = {
    one: { label: 'One card', positions: ['The card'] },
    three: { label: 'Three cards', positions: ['Past', 'Present', 'Future'] },
    celtic: {
      label: 'Celtic Cross',
      positions: [
        'Covers (the present)', 'Crosses (the obstacle)', 'Beneath (the foundation)',
        'Behind (the recent past)', 'Crowns (the aim)', 'Before (the near future)',
        'Self', 'House (surroundings)', 'Hopes and fears', 'What will come',
      ],
    },
  };

  // Yes / No: three piles. Each pile stops at an Ace or after 13 cards.
  // An upright Ace is a yes, a reversed Ace is a no. Reversed cards are always on.
  const ACES = CARDS.filter((c) => c.name.startsWith('Ace of ')).map((c) => c.id);
  SPREADS.yesno = {
    label: 'Yes / No',
    piles: { count: 3, max: 13, stopCards: ACES },
    pileNames: ['Pile 1', 'Pile 2', 'Pile 3'],
    reversals: 'always',
  };

  const api = { CARDS, SPREADS, ACES };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SpiritDeck = api;
})(typeof window !== 'undefined' ? window : globalThis);
