Board 6x6. Columns A-F, rows 1-6. Enemy has 3 packages: size 4, 3, 2. Must sink all. 50 turns. Every shot must count.

Shoot checkerboard pattern. Skip every other cell. Guarantees hit on any package size 2+. No wasted shots.

Order: A1, A3, A5, C1, C3, C5, E1, E3, E5, B2, B4, B6, D2, D4, D6, F2, F4, F6. Fill gaps after.

Never shoot same cell twice. Track all shots. Never revisit.

On HIT, stop hunt. Switch to KILL MODE.

1. Probe all 4 neighbors of hit cell. Order: UP, DOWN, LEFT, RIGHT. Skip already-shot cells.
2. Second hit found = package is a line. Know direction now (H or V). Extend both ways until sunk.
3. Miss at one end = flip. Go opposite end of all known hits. Extend until sunk.
4. Package sunk = resume hunt checkerboard where left off.

Never shoot diagonal. Packages only go straight.
Never shoot outside board. A0 not exist. G1 not exist.

Two packages hit, neither sunk = chase bigger one first. Bigger = more cells = faster complete kill = better tiebreak score.

Turn 40+, 2+ packages still alive = forget partial kills, sweep unchecked cells fast. More hits = better tiebreak.

Priority order:
1. Finish wounded package (KILL MODE active).
2. Hunt checkerboard (no active target).
3. Endgame sweep (turn 40+).
4. Never repeat shot.
5. Never leave board bounds.

Track every turn:
- All cells shot
- Active kill target cells
- Known package direction (H / V / unknown)
- Sunk package count
- Smallest remaining package size

After package sunk: skip its neighbors during hunt. Already eliminated.

Late game: any cell where no unshot line of smallest remaining size fits in any direction = skip it. Cannot hide there. Save turns for real targets.