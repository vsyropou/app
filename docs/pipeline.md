# Pipeline

A declared, YAML-driven data flow that runs in two places:

- **Offline** — batch data-prep pipelines via CLI (`app pipeline run <spec.yaml>`)
- **Online** — the serving surface wraps the *same* mechanism so `predict` is just another pipeline run (see [`app/models/functions.py`](../app/models/functions.py) + [`app/models/zero-shot-pipeline.yaml`](../app/models/zero-shot-pipeline.yaml))

One mechanism. Same transformers, sampler, sources, destinations — no second implementation.

## 1. YAML configuration

A spec lives in [`pipelines/`](../pipelines/) and describes 5 top-level blocks:

```yaml
name: data-preparation

source:      { type: csv,  params: { file_path: ./data/data.csv } }
adapter:     { type: field, params: { field: statement } }

transformers:
  - type: drop_nulls
    params: { fields: [Label] }
  - type: text_normalization
  - type: split_metadata
    params: { field: subjects, delimiter: "$" }
  - type: bucketize
    params:
      field: speaker_affiliation
      mapping: { republican: republican, democrat: democrat }

sampler:     { type: stratified, params: { label_field: Label, splits: { train: 0.8, validation: 0.1, test: 0.1 } } }
destination: { type: file, params: { filename: ./data/prepared.jsonl } }
```

Every block except `transformers` is optional. Loader: [`create_pipeline_from_config()`](../app/pipeline/config.py) returns `(source, pipeline, destination, adapter, sampler)`.

Each component is looked up by `type` against a registry ([`SOURCE_REGISTRY`](../app/pipeline/config.py), [`DESTINATION_REGISTRY`](../app/pipeline/config.py), [`ADAPTER_REGISTRY`](../app/pipeline/config.py), [`SAMPLER_REGISTRY`](../app/pipeline/config.py), [`TRANSFORMER_REGISTRY`](../app/pipeline/config.py)). Transformers are **auto-discovered** — walk [`app/pipeline/transformers/`](.), find `Transformer` subclasses with a `name` ClassVar, register. Sources/destinations/adapters/samplers are explicitly registered.

Each component is a pydantic `BaseModel`, so `params` from YAML validate at construction time.

## Optional blocks

| block | if omitted |
|-------|------------|
| `source` | `PipelineRunner` iterates `iter(None)` — effectively zero input. Useful for online (model) pipelines where the source is the request itself. |
| `adapter` | `NoopAdapter` passes each raw item through; assume already a `Document`. |
| `sampler` | stream flows raw (no split tag). |
| `destination` | required for `pipeline run`; absent in model pipelines (only `pipeline.process` is used). |

The `sampler:` block is consumed at construct-time, runs **post-transform** on `Document`s. Splits
are tagged on `metadata["split"]`.

## 2. Reusability — offline & online

Same `Pipeline` runs:

- **Offline (data prep)** — `uv run app pipeline run pipelines/data-preparation.yaml --batch-size 50`. Reads CSV, drops, cleans, buckets, dedups, stratifies, writes JSONL. Entry: [`app/cli/pipeline.py`](../app/cli/pipeline.py) → [`PipelineRunner`](../app/pipeline/runner.py).
- **Online (serving)** — `POST /api/v1/zero/predict` loads [`app/models/zero-shot-pipeline.yaml`](../app/models/zero-shot-pipeline.yaml), then `Pipeline.process(documents)` synchronously per request. See [`app/models/dependencies.py`](../app/models/dependencies.py) and [`app/models/functions.py`](../app/models/functions.py).

[`PipelineRunner.run()`](../app/pipeline/runner.py):

```python
for batch in chunk(iter(self.source), self.batch_size):
    documents = [self.adapter.adapt(item) for item in batch]
    all_docs.extend(self.pipeline.process(documents))

sampled = self.sampler.sample(all_docs) if self.sampler else iter(all_docs)
for doc in sampled:
    self.destination.ingest(doc)
```

Sampler runs **post-transform** on `Document`s (strata see the cleaned `source`). `batch_size` bounds source/adapter memory; the sampler buffers (same as polars DataFrame).

## Transformers

Each takes `Document` → `list[Document]` (one-to-many is allowed; drop by returning `[]`).

| type | what |
|------|------|
| `drop_nulls` | drop when source empty or listed metadata missing/empty |
| `filter-metadata` | whitelist metadata + impute defaults |
| `split_metadata` | `sub1$sub2` → `["sub1","sub2"]` (sorted) |
| `bucketize` | raw label → fixed bucket (e.g. `republican`/`democrat`/`other`/`none`) |
| `deduplicate` | drop `(source, speaker)` duplicates → prevents train/test leakage |
| `lowercase` `remove_stopwords` `remove_unicode` `text_normalization` `template` | source-text rewriting |
| `llm` | call an OpenAI-compatible endpoint with a JSON-schema response |

All live in [`cleaning.py`](../app/pipeline/transformers/cleaning.py); LLM-related in [`llm.py`](../app/pipeline/transformers/llm.py) and [`verdict.py`](../app/pipeline/transformers/verdict.py).
