"""Matplotlib chart builders — each returns a Figure for `st.pyplot`.

`df` accepts a polars or pandas DataFrame; Series of either kind has `.tolist`.
"""

import matplotlib.pyplot as plt


def _col(df, name: str) -> list:
    col = df[name]
    # pandas has .tolist(), polars has .to_list() — duck-type it
    return col.tolist() if hasattr(col, "tolist") else col.to_list()


def barh(title: str, df, top: int = 20) -> plt.Figure:
    """Horizontal bar of percentages (top-N). Ordinal Label kept in ORDERED order."""
    values, ns = _col(df, "value")[:top], _col(df, "n")[:top]
    total = sum(_col(df, "n"))
    pcts = [n / total * 100 for n in ns]
    values.reverse()
    pcts.reverse()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(values, pcts)
    ax.set_title(title)
    ax.set_xlabel("%")
    fig.tight_layout()
    return fig


def hist(title: str, series, bins: int = 40) -> plt.Figure:
    """Histogram of a numeric sequence (compact)."""
    fig, ax = plt.subplots(figsize=(4.5, 1.5))
    ax.hist(series, bins=bins)
    ax.set_title(title)
    ax.set_ylabel("count")
    fig.tight_layout()
    return fig


def heat(
    title: str,
    rows,
    cols,
    vals,
    ordinal_rows: list[str] | None = None,
    ordinal_cols: list[str] | None = None,
    top: int = 15,
) -> plt.Figure:
    """Heatmap of counts crosstab, log-scaled colors. Filters to top-N per axis.

    `ordinal_rows` / `ordinal_cols` (optional) — provided ordered list so axis shows in semantic order.
    """
    import math

    seen_rows, seen_cols = list(dict.fromkeys(rows)), list(dict.fromkeys(cols))
    top_rows = [r for r in ordinal_rows if r in seen_rows] if ordinal_rows else seen_rows[:top]
    top_cols = [c for c in ordinal_cols if c in seen_cols] if ordinal_cols else seen_cols[:top]
    grid = [[0] * len(top_cols) for _ in top_rows]
    row_idx = {v: i for i, v in enumerate(top_rows)}
    col_idx = {v: i for i, v in enumerate(top_cols)}
    for r, c, n in zip(rows, cols, vals):
        if r in row_idx and c in col_idx:
            grid[row_idx[r]][col_idx[c]] = n
    grid_log = [[math.log1p(v) if v else 0 for v in row] for row in grid]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.imshow(grid_log, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(top_cols)), top_cols, rotation=45, ha="right")
    ax.set_yticks(range(len(top_rows)), top_rows)
    ax.set_title(title)
    fig.tight_layout()
    return fig
