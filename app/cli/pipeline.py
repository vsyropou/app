from pathlib import Path
from typing import Annotated

import typer
from httpx import HTTPError
from rich.console import Console

from app.pipeline.config import create_pipeline_from_config
from app.pipeline.runner import PipelineRunner

app = typer.Typer(name="pipeline", help="Pipelines")

err_console = Console(stderr=True)


@app.command()
def run(
    spec: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            file_okay=True,
            dir_okay=False,
            help="The file containing the pipeline's specification",
        ),
    ],
    batch_size: Annotated[int, typer.Option(min=1, max=100, help="Number of source items to process per batch")] = 10,
) -> None:
    """
    Runs a pipeline.
    """
    try:
        source, pipeline, destination, adapter, sampler = create_pipeline_from_config(spec)
        runner = PipelineRunner(
            source=source,
            pipeline=pipeline,
            destination=destination,
            batch_size=batch_size,
            adapter=adapter,
            sampler=sampler,
        )
        runner.run()
    except ValueError as e:
        err_console.print(str(e))
    except HTTPError as e:
        err_console.print(str(e))
