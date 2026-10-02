import typer
from docker.errors import NotFound
from rich.console import Console

import docker

app = typer.Typer(name="ollama", help="Ollama Operations")

CONTAINER_NAME = "app-ollama"

error_console = Console(stderr=True, style="bold red")


@app.command()
def run(
    arguments: list[str] = typer.Argument(help="Arguments passed verbatim to `ollama` in the app-ollama container."),
) -> None:
    """Run any `ollama` command inside the app-ollama container (list, pull, ps, ...)."""

    client = docker.from_env()  # type: ignore[attr-defined]
    try:
        container = client.containers.get(CONTAINER_NAME)
    except NotFound:
        error_console.print(f"Container '{CONTAINER_NAME}' is not running. Start the stack first: make start-deps")
        raise typer.Exit(1)

    # ponytail: buffered output — no live progress for long pulls; stream=True + exec_inspect if that matters
    code, output = container.exec_run(["ollama", *arguments])
    typer.echo(output.decode(errors="replace") if isinstance(output, bytes) else output)
    raise typer.Exit(int(code))
