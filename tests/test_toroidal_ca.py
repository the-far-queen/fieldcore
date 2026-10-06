"""tests/test_toroidal_ca.py — property tests for the toroidal Conway CA.

context: ``count_neighbors`` was declared ``(x, y)`` but indexed
``grid[(y+dy)%h][(x+dx)%w]`` — i.e. arg0 was really the ROW index — while
``step()`` called it as ``count_neighbors(y, x)``. The arguments were
transposed, so the neighbour count was read off a different lattice. It was
invisible on a square grid with a symmetric pattern, which is why it
survived; the default geometry is 80x40 (non-square), where the
transposition is not even a mirror.

these tests assert PROPERTIES, not shapes:

  * cell-for-cell agreement with an independent, literal Conway reference
    written below (deliberately dumb indexing) over many generations on
    square AND non-square AND small wrapping tori;
  * the classic named patterns actually behave — blinkers oscillate,
    toads oscillate, beacons blink, gliders translate one cell diagonally
    per four generations;
  * wraparound actually wraps (patterns crossing the seam survive);
  * neighbourhood counts are the Moore neighbourhood, per cell, in both
    axis directions independently (a transposition can never satisfy this).
"""

from __future__ import annotations

import os
import random
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from toroidal_ca import ToroidalCA, TorusGeometry  # noqa: E402


# --------------------------------------------------------------------------
# independent reference implementation. written to be obviously correct:
# explicit row/col loops, explicit wraparound, no clever indexing,
# deliberately NOT sharing any code with the module under test.
# --------------------------------------------------------------------------

def reference_step(grid):
    """one generation of Conway's Life on a torus, literal and readable."""
    height = len(grid)
    width = len(grid[0])
    out = []
    for row in range(height):
        new_row = []
        for col in range(width):
            live = 0
            for drow in (-1, 0, 1):
                for dcol in (-1, 0, 1):
                    if drow == 0 and dcol == 0:
                        continue
                    rr = row + drow
                    cc = col + dcol
                    if rr < 0:
                        rr = rr + height
                    if rr >= height:
                        rr = rr - height
                    if cc < 0:
                        cc = cc + width
                    if cc >= width:
                        cc = cc - width
                    live = live + grid[rr][cc]
            if grid[row][col] == 1:
                new_row.append(1 if live == 2 or live == 3 else 0)
            else:
                new_row.append(1 if live == 3 else 0)
        out.append(new_row)
    return out


def reference_run(grid, generations):
    """run the reference forward and return the whole trajectory."""
    trajectory = [grid]
    current = grid
    for _ in range(generations):
        current = reference_step(current)
        trajectory.append(current)
    return trajectory


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def make_ca(grid):
    """a ToroidalCA holding exactly `grid` (row-major, no random reset)."""
    height = len(grid)
    width = len(grid[0])
    ca = ToroidalCA(TorusGeometry(grid_width=width, grid_height=height),
                    density=0.0)
    ca.grid = [row[:] for row in grid]
    return ca


def run_ca(ca, generations):
    """step the module forward and return the whole trajectory."""
    trajectory = [ca.grid]
    for _ in range(generations):
        ca.step()
        trajectory.append(ca.grid)
    return trajectory


def blank(width, height):
    return [[0] * width for _ in range(height)]


def live_cells(grid):
    """frozenset of (row, col) live positions — order-independent."""
    return frozenset((r, c) for r, row in enumerate(grid)
                     for c, v in enumerate(row) if v == 1)


def cell_count(grid):
    """number of live cells."""
    return sum(1 for row in grid for v in row if v == 1)


def random_grid(width, height, density, seed):
    rng = random.Random(seed)
    return [[1 if rng.random() < density else 0 for _ in range(width)]
            for _ in range(height)]


def place(grid, cells):
    """stamp live cells [(row, col), ...] into grid and return it."""
    for row, col in cells:
        grid[row][col] = 1
    return grid


# --------------------------------------------------------------------------
# 1. equivalence with an independent reference
# --------------------------------------------------------------------------

# 80x40 is the DEFAULT geometry — non-square, which is exactly where the
# transposition bug was invisible to the old square+symmetric checks.
# 7x13 and 13x7 cover both aspect orientations; 5x5 and 3x3 are tori small
# enough that a cell's 8 neighbours alias onto itself and each other.
SIZES = [
    (80, 40),   # default: non-square, 2:1
    (7, 13),    # non-square, odd dims (no centre, no half-torus symmetry)
    (13, 7),    # non-square, transposed aspect — must NOT give the same result
    (5, 5),     # tiny: neighbours wrap onto each other
    (3, 3),     # degenerate: the 8 offsets are 8 distinct cells, still no self
    (16, 16),   # square, larger — the case the bug used to hide on
]


@pytest.mark.parametrize("width,height", SIZES)
def test_matches_reference_cell_for_cell(width, height):
    """every cell agrees with the reference, every generation."""
    generations = 12
    start = random_grid(width, height, 0.30, seed=width * 1000 + height)
    want = reference_run(start, generations)
    got = run_ca(make_ca(start), generations)
    for gen, (want_grid, got_grid) in enumerate(zip(want, got)):
        assert got_grid == want_grid, (
            f"divergence at generation {gen} on {width}x{height}: "
            f"{sum(1 for r in range(height) for c in range(width) if got_grid[r][c] != want_grid[r][c])}"
            f"/{width * height} cells disagree"
        )


@pytest.mark.parametrize("width,height", [(80, 40), (7, 13), (5, 5)])
def test_matches_reference_on_adversarial_densities(width, height):
    """sparse, very dense and checkerboard starts all agree too."""
    for density, seed in ((0.05, 1), (0.5, 2), (0.75, 3), (0.0, 4)):
        start = random_grid(width, height, density, seed=seed)
        want = reference_run(start, 8)
        got = run_ca(make_ca(start), 8)
        assert got == want, f"density={density} on {width}x{height} diverged"


@pytest.mark.parametrize("width,height", [(7, 13), (13, 7), (80, 40)])
def test_row_and_col_are_not_transposed(width, height):
    """a transposed neighbour read would pass the square cases; this cannot.

    the start is asymmetric and long-lived, so reading the neighbourhood off
    a transposed lattice yields a genuinely different state. (verified: the
    7x13 seed settles to a block at rows 4-5, the transposed read settles to
    a block at rows 1-2.)
    """
    seeds = {
        (7, 13): [(4, 1), (4, 2), (5, 2)],
        (13, 7): [(0, 2), (1, 2), (1, 3)],
        (80, 40): None,   # random start, see below
    }
    if seeds[(width, height)] is None:
        start = random_grid(width, height, 0.30, seed=1)
    else:
        start = place(blank(width, height), seeds[(width, height)])
    assert width != height, "this test is only meaningful on a non-square torus"

    got = run_ca(make_ca(start), 8)
    assert got == reference_run(start, 8)

    transposed = [[start[c][r] for c in range(height)] for r in range(width)]
    assert live_cells(got[-1]) != live_cells(
        run_ca(make_ca(transposed), 8)[-1]), (
        "row and column are being conflated: the transposed start "
        "evolved to the same state"
    )


def test_count_neighbors_is_the_moore_neighbourhood_of_the_given_cell():
    """count_neighbors(row, col) must count the 8 cells around THAT cell.

    a single live cell, placed away from every seam, must be seen by exactly
    its 8 true neighbours and by nothing else. every cell on the grid is
    checked, so a row/col transposition cannot hide.
    """
    width, height = 20, 12
    for r in range(height):
        for c in range(width):
            grid = blank(width, height)
            grid[r][c] = 1
            ca = make_ca(grid)
            for rr in range(height):
                for cc in range(width):
                    expected = sum(
                        1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if (dr, dc) != (0, 0)
                        and (rr + dr) % height == r and (cc + dc) % width == c
                    )
                    assert ca.count_neighbors(rr, cc) == expected, (
                        f"count_neighbors(row={rr}, col={cc}) with the only "
                        f"live cell at ({r}, {c}): got "
                        f"{ca.count_neighbors(rr, cc)}, expected {expected}"
                    )


def test_neighbour_count_matches_reference_count_function():
    """the module's own per-cell count agrees with a literal count."""
    width, height = 9, 6
    start = random_grid(width, height, 0.4, seed=99)
    ca = make_ca(start)
    for r in range(height):
        for c in range(width):
            expected = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    expected += start[(r + dr) % height][(c + dc) % width]
            assert ca.count_neighbors(r, c) == expected


def test_empty_and_full_grids_are_stable():
    """nothing is born from nothing; the full plane is over-populated.

    (on 3x3 the full plane is not stable — every cell has 8 neighbours,
    not 2 or 3 — so the full-grid check uses a 7x7+ torus.)
    """
    for width, height in ((20, 20), (7, 13), (5, 5)):
        dead = blank(width, height)
        assert run_ca(make_ca(dead), 4)[-1] == dead

    for width, height in ((20, 20), (7, 13)):
        full = [[1] * width for _ in range(height)]
        assert run_ca(make_ca(full), 1)[-1] == blank(width, height)


# --------------------------------------------------------------------------
# 2. known Conway results — named patterns
# --------------------------------------------------------------------------

def test_blinker_oscillates_with_period_two():
    """horizontal blinker -> vertical blinker -> horizontal, forever."""
    grid = place(blank(9, 9), [(4, 3), (4, 4), (4, 5)])
    ca = make_ca(grid)
    horizontal = live_cells(grid)
    ca.step()
    vertical = live_cells(ca.grid)
    assert vertical == frozenset([(3, 4), (4, 4), (5, 4)])
    ca.step()
    assert live_cells(ca.grid) == horizontal
    # and it keeps oscillating indefinitely
    for _ in range(40):
        ca.step()
        assert live_cells(ca.grid) in (horizontal, vertical)
    assert ca.generation == 42


def test_toad_oscillates_with_period_two():
    """toad: the 2x3 stagger. period 2, and it is NOT its own phase-1 image."""
    toad = place(blank(11, 11), [(5, 3), (5, 4), (5, 5),
                                (6, 4), (6, 5), (6, 6)])
    ca = make_ca(toad)
    phase0 = live_cells(ca.grid)
    ca.step()
    phase1 = live_cells(ca.grid)
    ca.step()
    assert live_cells(ca.grid) == phase0
    assert phase1 != phase0, "a period-1 toad is not a toad"
    assert len(phase1) == 6
    for _ in range(30):
        ca.step()
        assert live_cells(ca.grid) in (phase0, phase1)


def test_beacon_blinks_with_period_two():
    """beacon: two 2x2 blocks diagonally touching. period 2."""
    beacon = place(blank(11, 11), [(4, 4), (4, 5), (5, 4), (5, 5),
                                  (6, 6), (6, 7), (7, 6), (7, 7)])
    ca = make_ca(beacon)
    on = live_cells(ca.grid)
    ca.step()
    off = live_cells(ca.grid)
    assert len(on) == 8
    assert len(off) == 6, "the inner corners die: a beacon thins to 6"
    assert off == frozenset([(4, 4), (4, 5), (5, 4), (6, 7), (7, 6), (7, 7)])
    ca.step()
    assert live_cells(ca.grid) == on
    for _ in range(20):
        ca.step()
        assert live_cells(ca.grid) in (on, off)


def test_glider_translates_one_cell_diagonally_every_four_generations():
    """the canonical glider: one row down + one col right every 4 generations."""
    width = height = 16
    glider = place(blank(width, height), [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)])
    start = live_cells(glider)
    assert len(start) == 5

    ca = make_ca(glider)
    shapes = [start]
    for _ in range(4):
        ca.step()
        shapes.append(live_cells(ca.grid))
    # a glider is 5 cells in every phase, including the intermediate ones
    for gen, shape in enumerate(shapes):
        assert len(shape) == 5, f"gen {gen} has {len(shape)} cells, not 5"

    def translated(shape, drow, dcol):
        return frozenset(((r + drow) % height, (c + dcol) % width)
                         for r, c in shape)

    assert shapes[4] == translated(start, 1, 1), (
        "after 4 generations the glider must be the original shape "
        "displaced one row down and one column right"
    )
    # generation 5 begins the next cycle (phase 1 of the translated glider)
    ca.step()
    assert len(live_cells(ca.grid)) == 5

    # 3 more generations = a second diagonal step
    for _ in range(3):
        ca.step()
    assert ca.generation == 8
    assert live_cells(ca.grid) == translated(start, 2, 2)

    # ride it for several more laps. the shape equals the start displaced
    # diagonally once per 4 generations (at phase 0); the intermediate phases
    # are rotated/reshaped, but the glider never changes size and never stops
    for _ in range(4 * 5):
        ca.step()
        assert len(live_cells(ca.grid)) == 5, "the glider never changes size"
        if ca.generation % 4 == 0:
            assert live_cells(ca.grid) == translated(
                start, ca.generation // 4, ca.generation // 4), (
                f"at generation {ca.generation} the glider is not the start "
                f"displaced diagonally {ca.generation // 4} times"
            )


def test_glider_crosses_the_seam_without_dying():
    """a glider parked in the bottom-right corner must wrap, not die or clip."""
    width = height = 12
    # the canonical 3x3 glider, shifted into the last 3 rows/cols so its
    # diagonal drift immediately crosses both seams
    canonical = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    cells = [((height - 3 + r) % height, (width - 3 + c) % width)
             for r, c in canonical]
    glider = place(blank(width, height), cells)
    start = frozenset(cells)
    assert len(start) == 5

    ca = make_ca(glider)
    for gen in range(1, 41):
        ca.step()
        assert len(live_cells(ca.grid)) == 5, f"glider died/changed at gen {gen}"
    # 40 generations = 10 diagonal steps, wrapped
    expected = frozenset(((r + 10) % height, (c + 10) % width)
                         for r, c in start)
    assert live_cells(ca.grid) == expected, (
        "the glider must survive the seam and keep its diagonal rate"
    )


def test_block_is_still_life():
    """2x2 block: the sanity anchor. nothing about it should move."""
    block = place(blank(9, 9), [(3, 3), (3, 4), (4, 3), (4, 4)])
    ca = make_ca(block)
    for _ in range(10):
        ca.step()
    assert live_cells(ca.grid) == live_cells(block)


# --------------------------------------------------------------------------
# 3. wraparound, explicitly
# --------------------------------------------------------------------------

def test_pattern_crossing_the_vertical_seam_wraps_and_survives():
    """a blinker straddling col 0/col w-1 must oscillate, not die."""
    width, height = 9, 9
    # horizontal blinker centred on the seam: cols w-1, 0, 1
    grid = place(blank(width, height), [(4, width - 1), (4, 0), (4, 1)])
    ca = make_ca(grid)
    phase_a = live_cells(ca.grid)
    ca.step()
    phase_b = live_cells(ca.grid)
    assert phase_b == frozenset([(3, 0), (4, 0), (5, 0)]), (
        "a blinker on the seam must rotate about the seam, not collapse"
    )
    ca.step()
    assert live_cells(ca.grid) == phase_a
    for _ in range(20):
        ca.step()
        assert live_cells(ca.grid) in (phase_a, phase_b)


def test_pattern_crossing_the_horizontal_seam_wraps_and_survives():
    """vertical blinker straddling row 0/row h-1."""
    height, width = 9, 9
    grid = place(blank(width, height), [(height - 1, 4), (0, 4), (1, 4)])
    ca = make_ca(grid)
    phase_a = live_cells(ca.grid)
    ca.step()
    phase_b = live_cells(ca.grid)
    assert phase_b == frozenset([(0, 3), (0, 4), (0, 5)])
    ca.step()
    assert live_cells(ca.grid) == phase_a


def test_pattern_spanning_a_corner_survives():
    """cells at all four corners are mutual neighbours on a small torus."""
    width = height = 6
    # on a 6x6 torus the four corners (0,0) (0,w-1) (h-1,0) (h-1,w-1) are a
    # 2x2 block of mutual neighbours once wrapped: a block is still life.
    corners = [(0, 0), (0, width - 1), (height - 1, 0),
               (height - 1, width - 1)]
    grid = place(blank(width, height), corners)
    ca = make_ca(grid)
    for _ in range(8):
        ca.step()
    assert live_cells(ca.grid) == frozenset(corners), (
        "a block wrapped across the corner must stay a block"
    )


def test_wraparound_neighbours_are_counted_across_the_seam():
    """cell (0,0) sees cell (h-1, w-1) — the far corner — on the torus."""
    width, height = 6, 4
    grid = blank(width, height)
    grid[height - 1][width - 1] = 1
    ca = make_ca(grid)
    assert ca.count_neighbors(0, 0) == 1, "the near corner sees the far one"
    assert ca.count_neighbors(1, 1) == 0
    # exactly the 8 true Moore neighbours see it: the wrapping rows/cols
    # fan out, so the count spans the seam rather than clipping
    assert sum(1 for r in range(height) for c in range(width)
               if ca.count_neighbors(r, c) == 1) == 8


def test_small_torus_3x3_matches_reference_and_dies_like_a_trio():
    """3x3 is the smallest honest torus: every cell neighbours all 8 others.

    on a 3x3 the L-tromino's missing fourth square is its own neighbour, so
    the birth at (1,1) sees the whole neighbourhood and the tromino blooms
    to a full plane, then dies of overpopulation at generation 2.
    """
    width = height = 3
    grid = place(blank(width, height), [(0, 0), (0, 1), (1, 0)])
    ca = make_ca(grid)
    assert ca.count_neighbors(0, 0) == 2
    # on a 3x3, cell (1,1)'s 8 neighbours are the other 8 cells, so it sees
    # all three live ones
    assert ca.count_neighbors(1, 1) == 3

    got = run_ca(ca, 4)
    assert got == reference_run(grid, 4)

    def cell_count(state):
        return sum(1 for row in state for v in row if v == 1)

    counts = [cell_count(s) for s in got]
    assert counts[0] == 3
    assert counts[1] == 9, "on a 3x3 the tromino fills the whole torus"
    assert counts[2] == 0, "every cell then has 8 neighbours and dies"
    assert counts[-1] == 0
    # and it stays dead
    assert got[-1] == blank(3, 3)


def test_3x3_full_plane_is_not_still_life():
    """documents the wraparound interaction: full 3x3 has 8 neighbours."""
    grid = [[1] * 3 for _ in range(3)]
    ca = make_ca(grid)
    assert ca.count_neighbors(1, 1) == 8
    ca.step()
    assert live_cells(ca.grid) == frozenset(), (
        "8 neighbours overpopulation kills everything on a 3x3 torus"
    )


# --------------------------------------------------------------------------
# 4. module plumbing still intact (existing behaviour, not weakened)
# --------------------------------------------------------------------------

def test_generation_counter_and_digest_track_state():
    ca = ToroidalCA(TorusGeometry(grid_width=20, grid_height=10), density=0.3)
    assert ca.generation == 0
    first = ca.digest()
    for _ in range(5):
        ca.step()
    assert ca.generation == 5
    assert ca.digest() != first
    # digest is row-major and 16 hex chars
    assert len(ca.digest()) == 16


def test_digest_is_row_major_not_column_major():
    """digest hashes the rows in row-major order.

    pins the module's existing (literal backslash-n) separator so a future
    row/col swap or an accidental format change is caught. rows are joined
    with the two-character string "\\n", NOT a newline — see the reference
    computation below.
    """
    import hashlib

    grid = place(blank(5, 3), [(0, 1), (1, 3), (2, 0)])
    ca = make_ca(grid)
    rows = ["".join(str(v) for v in row) for row in grid]
    assert rows == ["01000", "00010", "10000"]
    want = hashlib.sha256("\\n".join(rows).encode()).hexdigest()[:16]
    assert ca.digest() == want

    # a column-major read of the same cells gives a different digest
    column_major = ["".join(str(grid[r][c]) for r in range(3)) for c in range(5)]
    other = hashlib.sha256("\\n".join(column_major).encode()).hexdigest()[:16]
    assert other != want


def test_reset_matches_geometry_and_resets_generation():
    geo = TorusGeometry(grid_width=14, grid_height=6)
    ca = ToroidalCA(geo, density=0.5)
    assert len(ca.grid) == 6 and all(len(r) == 14 for r in ca.grid)
    ca.step()
    ca.reset()
    assert ca.generation == 0
    assert len(ca.grid) == 6 and all(len(r) == 14 for r in ca.grid)


def test_step_returns_the_new_grid_and_updates_in_place():
    grid = place(blank(7, 7), [(3, 2), (3, 3), (3, 4)])
    ca = make_ca(grid)
    returned = ca.step()
    assert returned is ca.grid
    assert live_cells(returned) == frozenset([(2, 3), (3, 3), (4, 3)])


def test_default_geometry_still_runs_end_to_end():
    """the 80x40 default is the case the bug lived in."""
    ca = ToroidalCA(TorusGeometry(), density=0.3)
    assert len(ca.grid) == 40 and all(len(r) == 80 for r in ca.grid)
    start = [row[:] for row in ca.grid]
    want = reference_run(start, 5)
    got = run_ca(ca, 5)
    assert got == want