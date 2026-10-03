from pathlib import Path

import typer

from app.pipeline.config import create_pipeline_from_config
from app.pipeline.runner import PipelineRunner

app = typer.Typer(name="model", help="Model Operations")


@app.command()
def prepare(
    spec: Path = typer.Option(
        Path("pipelines/tuning.yaml"),
        "--spec",
        help="Pipeline spec for sampling + prompt building.",
    ),
    batch_size: int = typer.Option(500, "--batch-size"),
) -> None:
    """Build tune.jsonl via the tuning pipeline (CSV → stratified splits → chat records)."""
    source, pipeline, destination, adapter, sampler = create_pipeline_from_config(spec)
    runner = PipelineRunner(
        source=source,
        pipeline=pipeline,
        destination=destination,
        batch_size=batch_size,
        adapter=adapter,
        sampler=sampler,
    )
    n = runner.run()
    typer.echo(f"wrote {n} examples via {spec}")


@app.command()
def tune(
    jsonl_path: Path = typer.Argument(..., help="Chat-format jsonl produced by `model prepare`."),
    base_model: str = typer.Option("Qwen/Qwen2.5-0.5B-Instruct", "--base-model"),
    out_dir: Path = typer.Option(Path("models/factcheck"), "--out"),
    epochs: int = typer.Option(1, "--epochs"),
) -> None:
    """LoRA fine-tune base_model on jsonl_path."""
    from app.models import tune as t

    t.run_tuning(jsonl_path, base_model, out_dir, epochs)
    typer.echo(f"adapter saved to {out_dir}")
