"""Generic ephemeral-container runner: build once per deps-toml, run any command inside."""

import hashlib
from logging import getLogger
from pathlib import Path
from typing import Any

from docker.errors import BuildError

import docker

logger = getLogger(__name__)


def _image_tag(deps_toml: Path) -> str:
    return "model:" + hashlib.sha256(deps_toml.read_bytes()).hexdigest()[:12]


def _ensure_image(client: Any, tag: str, context: Path) -> None:
    try:
        client.images.get(tag)
        logger.info("Using cached image %s", tag)
        return
    except docker.errors.ImageNotFound:
        pass
    logger.info("Building image %s", tag)
    (context / "Dockerfile").write_text(DOCKERFILE)
    try:
        client.images.build(tag=tag, path=str(context), rm=True)
    except BuildError as e:
        logger.error("Image build failed: %s", e)
        raise


def run_in_container(
    command: list[str],
    deps_toml: Path,
    artifact_path: Path,
    extra_paths: list[Path] | None = None,
) -> int:
    """Run `command` inside an ephemeral container built from the model dir + deps.

    :param command: the command to run (e.g. ["python", "-m", "app.model.train"]).
    :param config: pydantic settings; serialized to config.json, readable via MODEL_CONFIG env.
    :param deps_toml: pyproject-format TOML with [project] dependencies.
    :param artifact_path: host dir bind-mounted rw at /artifacts (ARTIFACTS env inside).
    :param extra_paths: optional extra host paths copied into the build context.
    :return: the container exit code.
    """

    client = docker.from_env()  # type: ignore[attr-defined]
    tag = _image_tag(deps_toml)
    artifact_path.mkdir(parents=True, exist_ok=True)

    context = _build_context(MODEL_DIR, deps_toml, config_json, extra_paths or [])
    try:
        _ensure_image(client, tag, context)
        logger.info("Running %s in %s", command, tag)
        container = client.containers.run(
            tag,
            command=command,
            volumes={str(artifact_path.resolve()): {"bind": "/artifacts", "mode": "rw"}},
            environment={"PYTHONPATH": "/workspace/model"},
            detach=True,
        )
        try:
            for line in container.logs(stream=True, follow=True):
                print(f"[container] {line.decode(errors='replace').rstrip()}")
            status = container.wait()
            code: Any = status.get("StatusCode", 1)
            return int(code)
        finally:
            container.remove(force=True)
    finally:
        shutil.rmtree(context, ignore_errors=True)
        config_json.unlink(missing_ok=True)
