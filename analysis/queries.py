"""DuckDB analytical queries for the labeled-statement analysis."""

from functools import cache
from pathlib import Path

import duckdb

ORDERED_LABELS = ["extremely-false", "false", "barely-true", "half-true", "mostly-true", "true"]

_SOURCE = Path(__file__).parent.parent / "data" / "data.csv"


def set_source(path: Path) -> None:
    """Re-point the view and bust all `@cache` query results."""
    global _SOURCE
    _SOURCE = path
    for fn in (counts, counts_exploded, word_counts, crosstab, crosstab_exploded, label_crosstab):
        fn.cache_clear()


def _view_sql(path: Path) -> str:
    """CSV: plain. JSONL: flatten {source, metadata.*}, join list subjects with '$'."""
    if path.suffix == ".jsonl":
        return f"""
            SELECT
                metadata.Label AS Label,
                source AS statement,
                ARRAY_TO_STRING(metadata.subjects::VARCHAR[], '$') AS subjects,
                metadata.speaker_name AS speaker_name,
                metadata.speaker_job AS speaker_job,
                metadata.speaker_state AS speaker_state,
                metadata.speaker_affiliation AS speaker_affiliation,
                metadata.statement_context AS statement_context
            FROM read_json('{path}', format='newline_delimited',
                         columns={{source: 'VARCHAR', metadata: 'STRUCT(Label VARCHAR, subjects VARCHAR[], speaker_name VARCHAR, speaker_job VARCHAR, speaker_state VARCHAR, speaker_affiliation VARCHAR, statement_context VARCHAR)'}})
        """
    return f"SELECT * FROM read_csv_auto('{path}', header=true)"


def _con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"CREATE OR REPLACE VIEW data AS {_view_sql(_SOURCE)}")
    return con


@cache
def counts(col: str) -> duckdb.DuckDBPyRelation:
    """Plain categorical counts; NULL/empty → '<Unknown>'. Ordinal Label reorders by ORDERED_LABELS."""
    if col == "Label":
        return _con().query(
            "SELECT Label AS value, COUNT(*) AS n FROM data GROUP BY 1 ORDER BY CASE value "
            + " ".join(f"WHEN '{l}' THEN {i}" for i, l in enumerate(ORDERED_LABELS))
            + " END"
        )
    return _con().query(
        f"SELECT COALESCE(NULLIF(CAST({col} AS VARCHAR), ''), '<Unknown>') AS value, COUNT(*) AS n "
        f"FROM data GROUP BY 1 ORDER BY n DESC"
    )


@cache
def counts_exploded(col: str) -> duckdb.DuckDBPyRelation:
    """Counts on a `$`-delimited column, unnested per part; NULL/empty → '<Unknown>'."""
    return _con().query(
        f"""
        SELECT COALESCE(NULLIF(TRIM(part), ''), '<Unknown>') AS value, COUNT(*) AS n
        FROM (SELECT UNNEST(string_split({col}, '$')) AS part FROM data)
        GROUP BY 1 ORDER BY n DESC
        """
    )


@cache
def word_counts() -> duckdb.DuckDBPyRelation:
    """One int per statement: word count."""
    return _con().query("SELECT ARRAY_LENGTH(string_split(statement, ' '), 1) AS words FROM data")


@cache
def crosstab(col_a: str, col_b: str) -> duckdb.DuckDBPyRelation:
    """Pivot (col_a, col_b) counts for heatmap."""
    return _con().query(f"SELECT {col_a} AS row_value, {col_b} AS col_value, COUNT(*) AS n FROM data GROUP BY 1, 2")


@cache
def crosstab_exploded(col_a: str, col_b: str) -> duckdb.DuckDBPyRelation:
    """col_a may be `$`-delimited — unnest before group-by."""
    return _con().query(
        f"""
        SELECT U.part AS row_value, {col_b} AS col_value, COUNT(*) AS n
        FROM (SELECT UNNEST(string_split({col_a}, '$')) AS part, {col_b} FROM data) AS U
        GROUP BY 1, 2
        """
    )


@cache
def label_crosstab(col: str) -> duckdb.DuckDBPyRelation:
    """Label vs col counts."""
    return crosstab("Label", col)
