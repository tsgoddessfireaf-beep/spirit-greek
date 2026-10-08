"""Designed left half of the "aeonicarts" ambigram (a e o n i | c a r t s).

Each slot reads as its own letter, and its half-turned copy reads as the partner:
a~s, e~t, o~r, n~a, i~c. Local coordinates: x about the slot centre, baseline y = 0,
x-height y = 100. Turned over, a local point (x, y) becomes (-x, 100 - y).
"""

# a ~ s : italic one-storey a, pointed at the foot. Turned over, the slanted stem is
# the hairline up-stroke of a cursive s and the bowl is its belly.
a = {'strokes': [
    {'pts': [(19, 96), (12, 48), (5, 2)], 'nib': 6, 'hair': 2.6},                       # stem: a hairline
    {'pts': [(5, 2), (-6, 10), (-10, 24), (-20, 56), (-14, 88), (0, 100), (14, 99), (19, 96)]},  # bowl
]}

# e ~ t : e whose bar runs out to the left and whose back runs down into a tail.
# Turned over: the back is the t's stem rising above the x-height, crossed by the bar.
e = {'strokes': [
    {'pts': [(-34, 48), (-10, 52), (14, 58)], 'taper': (0.5, 0)},                     # bar
    {'pts': [(14, 58), (16, 84), (2, 100), (-12, 88), (-16, 55), (-16, 10), (-14, -22), (-6, -34)],
     'taper': (0, 0.3)},
]}

# o ~ r : the o's right side is the r's stem, its bottom the r's shoulder (ending in a
# ball), its top the r's foot. The o is open at the upper left.
o = {'strokes': [
    {'pts': [(-16, 56), (-19, 26), (-6, 1), (8, 2), (17, 20), (18, 60), (16, 88)]},     # left, bottom, right
    {'pts': [(16, 88), (6, 99), (-6, 97)], 'nib': 4, 'hair': 2.4},                      # top: a hairline
], 'dots': [(-16, 58, 4)]}

# n ~ a : n with a fine hairline under its foot. Turned over: a one-storey a.
n = {'strokes': [
    {'pts': [(-30, 86), (-19, 100), (-19, 50), (-19, 0)], 'taper': (0.3, 0)},          # entry + left stem
    {'pts': [(-19, 66), (-8, 96), (8, 98), (18, 74), (19, 30), (18, 6)]},                # arch + right stem
    {'pts': [(18, 6), (4, -1), (-12, 4)], 'nib': 7, 'hair': 2.6},                        # hairline closure
]}

# i ~ c : a straight stem with a lead-in flick and a ball foot. Turned over:
# a narrow c (ball at top right, exit at bottom right). The dot becomes a star.
i = {'strokes': [
    {'pts': [(-12, 84), (2, 99), (8, 92), (10, 50), (8, 12), (0, 2), (-10, 6)]},
], 'dots': [(8, 134, 9)]}

v1 = {'glyphs': [a, e, o, n, i], 'pitch': 60}
