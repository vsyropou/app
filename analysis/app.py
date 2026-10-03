"""Streamlit entry point for the labeled-statement analysis."""

from pathlib import Path

import duckdb
import streamlit as st

from analysis import charts, queries
from analysis.charts import _col

DATA_DIR = Path("data")
SUPPORTED = {".csv", ".jsonl"}
files = sorted([p for p in DATA_DIR.iterdir() if p.suffix in SUPPORTED])

st.set_page_config(layout="wide")
st.title("Labeled statement analysis")

choice = st.sidebar.selectbox("Source", [p.name for p in files])
queries.set_source(DATA_DIR / choice)

st.header("SQL explorer")
sql = st.text_area("Query the `data` view", value="SELECT * FROM data LIMIT 10", height=120)
if st.button("Run"):
    try:
        con = duckdb.connect()
        con.execute(f"CREATE VIEW data AS {queries._view_sql(queries._SOURCE)}")
        st.dataframe(con.execute(sql).pl())
    except duckdb.Error as e:
        st.error(str(e))

ANALYSES = [
    ("Label", queries.counts("Label")),
    ("Subject", queries.counts_exploded("subjects")),
    ("Speaker", queries.counts("speaker_name")),
    ("Speaker job", queries.counts("speaker_job")),
    ("Speaker state", queries.counts("speaker_state")),
    ("Affiliation", queries.counts("speaker_affiliation")),
    ("Context", queries.counts("statement_context")),
]

PER_ROW = 3
for i in range(0, len(ANALYSES), PER_ROW):
    for col, (label, rel) in zip(st.columns(PER_ROW), ANALYSES[i : i + PER_ROW]):
        df = rel.pl()
        col.subheader(f"{label} (count={len(df)})")
        col.pyplot(charts.barh(label, df))

words = queries.word_counts().pl()["words"].to_list()
col1, _col2 = st.columns([1.15, 5])
col1.header("Statement word count")
col1.pyplot(charts.hist("Statement word counts", words))

st.header("Pairwise: Label × categorical")
PAIR_COLS = [
    ("Subject", "subjects", True),
    ("Speaker", "speaker_name", False),
    ("Speaker job", "speaker_job", False),
    ("Speaker state", "speaker_state", False),
    ("Affiliation", "speaker_affiliation", False),
    ("Context", "statement_context", False),
]
PER_ROW = 3
for i in range(0, len(PAIR_COLS), PER_ROW):
    for col, (label, name, exploded) in zip(st.columns(PER_ROW), PAIR_COLS[i : i + PER_ROW]):
        get = queries.crosstab_exploded("Label", name) if exploded else queries.label_crosstab(name)
        df = get.pl()
        rows, cols, vals = _col(df, "col_value"), _col(df, "row_value"), _col(df, "n")
        col.pyplot(charts.heat(f"{label} × Label", rows, cols, vals, ordinal_cols=queries.ORDERED_LABELS))

st.header("Custom pair")
c1, _c2 = st.columns([1, 1])
with c1:
    col_a_sel = st.selectbox("rows", [c[1] for c in PAIR_COLS] + ["Label"])
    col_b_sel = st.selectbox("cols", [c[1] for c in PAIR_COLS] + ["Label"])
    df = queries.crosstab(col_a_sel, col_b_sel).pl()
    st.pyplot(
        charts.heat(
            f"{col_a_sel} × {col_b_sel}",
            _col(df, "row_value"),
            _col(df, "col_value"),
            _col(df, "n"),
            ordinal_rows=queries.ORDERED_LABELS if col_a_sel == "Label" else None,
            ordinal_cols=queries.ORDERED_LABELS if col_b_sel == "Label" else None,
        )
    )
