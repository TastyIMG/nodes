"""
Pure numpy port of the shape-edge detection algorithms from the HTML prototype (app.js).
No dependencies beyond numpy.
"""
import numpy as np


def build_alpha_grid(mask_2d):
    """Convert a 2D mask (float 0-1) to a binary uint8 grid (1=opaque, 0=transparent)."""
    return (mask_2d > 0).astype(np.uint8)


def find_edge_rows(grid, min_run):
    """
    Horizontal edge detection — port of findStraightEdgeRows().
    For each row, finds the longest contiguous run of boundary pixels.
    A boundary pixel: opaque, and the pixel above OR below is transparent.
    Returns list of (coord, score) tuples.
    """
    h, w = grid.shape
    results = []

    for y in range(h):
        run_len = 0
        max_run = 0
        for x in range(w):
            if grid[y, x]:
                above = grid[y - 1, x] if y > 0 else 0
                below = grid[y + 1, x] if y < h - 1 else 0
                if not above or not below:
                    run_len += 1
                    if run_len > max_run:
                        max_run = run_len
                    continue
            run_len = 0
        if max_run >= min_run:
            results.append((y, max_run))

    return results


def find_edge_cols(grid, min_run):
    """
    Vertical edge detection — port of findStraightEdgeCols().
    For each column, finds the longest contiguous run of boundary pixels.
    A boundary pixel: opaque, and the pixel left OR right is transparent.
    Returns list of (coord, score) tuples.
    """
    h, w = grid.shape
    results = []

    for x in range(w):
        run_len = 0
        max_run = 0
        for y in range(h):
            if grid[y, x]:
                left = grid[y, x - 1] if x > 0 else 0
                right = grid[y, x + 1] if x < w - 1 else 0
                if not left or not right:
                    run_len += 1
                    if run_len > max_run:
                        max_run = run_len
                    continue
            run_len = 0
        if max_run >= min_run:
            results.append((x, max_run))

    return results


def find_diag45_edges(grid, min_run):
    """
    45-degree diagonal edge detection — port of findDiag45Edges().
    Diagonals where x - y = constant. Boundary check: upper-right or lower-left is transparent.
    Returns list of (coord, score) tuples where coord = x - y.
    """
    h, w = grid.shape
    results = []

    for d in range(-(h - 1), w):
        start_x = max(0, d)
        start_y = start_x - d
        run_len = 0
        max_run = 0
        x, y = start_x, start_y
        while x < w and y < h:
            if grid[y, x]:
                ur = grid[y - 1, x + 1] if (y > 0 and x < w - 1) else 0
                ll = grid[y + 1, x - 1] if (y < h - 1 and x > 0) else 0
                if not ur or not ll:
                    run_len += 1
                    if run_len > max_run:
                        max_run = run_len
                    x += 1; y += 1
                    continue
            run_len = 0
            x += 1; y += 1
        if max_run >= min_run:
            results.append((d, max_run))

    return results


def find_diag135_edges(grid, min_run):
    """
    135-degree diagonal edge detection — port of findDiag135Edges().
    Diagonals where x + y = constant. Boundary check: upper-left or lower-right is transparent.
    Returns list of (coord, score) tuples where coord = x + y.
    """
    h, w = grid.shape
    results = []

    for s in range(0, (w - 1) + (h - 1) + 1):
        start_x = min(s, w - 1)
        start_y = s - start_x
        run_len = 0
        max_run = 0
        x, y = start_x, start_y
        while x >= 0 and y < h:
            if grid[y, x]:
                ul = grid[y - 1, x - 1] if (y > 0 and x > 0) else 0
                lr = grid[y + 1, x + 1] if (y < h - 1 and x < w - 1) else 0
                if not ul or not lr:
                    run_len += 1
                    if run_len > max_run:
                        max_run = run_len
                    x -= 1; y += 1
                    continue
            run_len = 0
            x -= 1; y += 1
        if max_run >= min_run:
            results.append((s, max_run))

    return results


def merge_nearby(candidates, tol):
    """
    Port of mergeNearby() — clusters edges within tolerance, keeps the one with highest score.
    candidates: list of (coord, score) tuples
    Returns: list of coord ints
    """
    if not candidates:
        return []

    candidates = sorted(candidates, key=lambda c: c[0])
    merged = []
    group = [candidates[0]]

    for i in range(1, len(candidates)):
        if candidates[i][0] - group[-1][0] <= tol:
            group.append(candidates[i])
        else:
            merged.append(_best_in_group(group))
            group = [candidates[i]]

    merged.append(_best_in_group(group))
    return merged


def _best_in_group(group):
    """Return the coord of the candidate with the highest score."""
    best = group[0]
    for item in group[1:]:
        if item[1] > best[1]:
            best = item
    return best[0]


def compute_all_edges(mask_2d, edge_min, merge_tol):
    """
    Full pipeline: build grid, detect all 4 edge types, merge.
    Returns dict with keys: h_lines, v_lines, d45_lines, d135_lines (each a list of ints).
    """
    grid = build_alpha_grid(mask_2d)

    h_candidates = find_edge_rows(grid, edge_min)
    v_candidates = find_edge_cols(grid, edge_min)
    d45_candidates = find_diag45_edges(grid, edge_min)
    d135_candidates = find_diag135_edges(grid, edge_min)

    return {
        "h_lines": merge_nearby(h_candidates, merge_tol),
        "v_lines": merge_nearby(v_candidates, merge_tol),
        "d45_lines": merge_nearby(d45_candidates, merge_tol),
        "d135_lines": merge_nearby(d135_candidates, merge_tol),
    }
