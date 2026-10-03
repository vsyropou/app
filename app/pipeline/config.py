"""
YAML configuration for pipeline components.
"""

import importlib
import inspect
import pkgutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel, Field

from app.pipeline.adapters import Adapter, FieldExtractorDocumentAdapter, NoopAdapter
from app.pipeline.base import Pipeline
from app.pipeline.destinations.base import Destination
from app.pipeline.destinations.io import FileDestination
from app.pipeline.samplers import Sampler, StratifiedSampler
from app.pipeline.sources.base import Source
from app.pipeline.sources.csv import CSVSource
from app.pipeline.sources.filesystem import FilesystemSource
from app.pipeline.sources.jsonl import JSONLSource
from app.pipeline.transformers.base import Transformer


class BasePipelineConfig(BaseModel):
    class Config:
        extra = "forbid"


class SourceConfig(BasePipelineConfig):
    """Configuration for the source of the pipeline."""

    type: str = Field(..., description="The name of the source.")
    name: str | None = Field(None, description="Optional name for the source.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to initialize the source.")


class DestinationConfig(BasePipelineConfig):
    """Configuration for the destination of the pipeline."""

    type: str = Field(..., description="The name of the destination.")
    name: str | None = Field(None, description="Optional name for the destination.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to initialize the destination.")


class TransformerConfig(BasePipelineConfig):
    """Configuration for a transformer in the pipeline."""

    type: str = Field(..., description="The name of the transformer.")
    name: str | None = Field(None, description="Optional name for the transformer.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to initialize the transformer.")


class AdapterConfig(BasePipelineConfig):
    """Configuration for an adapter in the pipeline."""

    type: str = Field(..., description="The name of the adapter.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to initialize the adapter.")


class SamplerConfig(BasePipelineConfig):
    """Configuration for a sampler between source and adapter."""

    type: str = Field(..., description="The name of the sampler.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters to initialize the sampler.")


class PipelineConfig(BasePipelineConfig):
    """Configuration for a complete pipeline."""

    class Config:
        extra = "forbid"

    name: str = Field(..., description="The name of the pipeline.")
    description: str | None = Field(None, description="Optional description of the pipeline.")
    source: SourceConfig | None = Field(None, description="The source of the documents to process in the pipeline.")
    transformers: list[TransformerConfig] = Field(None, description="List of transformers to include in the pipeline.")
    destination: DestinationConfig | None = Field(
        None, description="The destination for processed documents in the pipeline."
    )
    adapter: AdapterConfig | None = Field(
        None, description="Optional adapter for converting source items to documents."
    )
    sampler: SamplerConfig | None = Field(
        None, description="Optional sampler between source and adapter for stratified splits."
    )


# List of known sources
SOURCE_REGISTRY: dict[str, type[Source]] = {
    CSVSource.name: CSVSource,
    JSONLSource.name: JSONLSource,
    FilesystemSource.name: FilesystemSource,
}

# Registry of destination implementations
DESTINATION_REGISTRY: dict[str, type[Destination[Any]]] = {FileDestination.name: FileDestination}

# Registry of adapter implementations
ADAPTER_REGISTRY: dict[str, type[Adapter]] = {adapter.name: adapter for adapter in [FieldExtractorDocumentAdapter]}

# Registry of samplers; sits between source and adapter.
SAMPLER_REGISTRY: dict[str, type[Sampler]] = {s.name: s for s in [StratifiedSampler]}


def get_transformer_registry() -> dict[str, type[Transformer]]:
    """
    Dynamically build a registry of all available transformers.

    :return: A dictionary mapping transformer names to transformer classes.
    """
    from app.pipeline import transformers

    registry = {}

    # Walk through all modules in the pipeline package
    package_dir = Path(transformers.__file__).parent
    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if is_pkg or module_name == "transformer" or module_name == "base" or module_name == "config":
            continue

        # Import the module
        module = importlib.import_module(f"app.pipeline.transformers.{module_name}")

        # Find all Transformer subclasses in the module
        for _name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Transformer)
                and obj is not Transformer
                and hasattr(obj, "name")
            ):
                registry[obj.name] = obj

    return registry


# Build the registry once at module import time
TRANSFORMER_REGISTRY = get_transformer_registry()


def load_pipeline_config(config_path: str | Path) -> PipelineConfig:
    """
    Load a pipeline configuration from a YAML file.
    :param config_path: Path to the YAML configuration file.

    :return: The parsed pipeline configuration.

    :raise FileNotFoundError: If the config file doesn't exist.
    :raise ValueError: If the YAML is invalid or doesn't match the expected schema.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    return PipelineConfig.model_validate(config_data, strict=True)


def create_component_from_config(
    config: SourceConfig | DestinationConfig | TransformerConfig | AdapterConfig | SamplerConfig,
) -> tuple[str | None, Source | Destination[Any] | Transformer | Adapter | Sampler]:
    """
    Create a pipeline component (source, destination, transformer, adapter, or sampler) from its configuration.

    :param config: The component configuration.
    :return: A tuple of (name, component_instance). Name may be None for components that don't have names.
    :raises ValueError: If component_type is unknown or the specified type doesn't exist in the registry.
    """
    registry: Mapping[str, type[Source | Destination[Any] | Transformer | Adapter | Sampler]]
    if isinstance(config, SourceConfig):
        registry = SOURCE_REGISTRY
    elif isinstance(config, TransformerConfig):
        registry = TRANSFORMER_REGISTRY
    elif isinstance(config, DestinationConfig):
        registry = DESTINATION_REGISTRY
    elif isinstance(config, AdapterConfig):
        registry = ADAPTER_REGISTRY
    elif isinstance(config, SamplerConfig):
        registry = SAMPLER_REGISTRY
    else:
        raise ValueError("Unexpected configuration type")

    if config.type not in registry:
        raise ValueError(f"Unknown type: {config.type}. Available types: {list(registry.keys())}")

    component_cls = registry[config.type]
    component_instance = component_cls(**config.params)

    # Only SourceConfig, TransformerConfig and DestinationConfig have name field
    name = getattr(config, "name", None)

    return name, component_instance


def create_adapter_from_config(config: AdapterConfig | None) -> Adapter:
    """
    Create an adapter instance from its configuration.

    :param config: The adapter configuration, or None to use the default adapter.
    :return: The adapter instance.
    """
    if config is None:
        return NoopAdapter()

    _, adapter = cast(tuple[None, Adapter], create_component_from_config(config))
    return adapter


def create_sampler_from_config(config: SamplerConfig | None) -> Sampler | None:
    """
    Create a sampler instance from its configuration.

    :param config: The sampler configuration, or None to skip sampling.
    :return: The sampler instance, or None.
    """
    if config is None:
        return None

    _, sampler = cast(tuple[None, Sampler], create_component_from_config(config))
    return sampler


def create_pipeline_from_config(
    config: PipelineConfig | str | Path,
) -> tuple[Source | None, Pipeline, Destination[Any], Adapter, Sampler | None]:
    """
    Create a pipeline from a configuration.

    :param config: Either a PipelineConfig object or a path to a YAML configuration file.
    :return: A tuple of (source, pipeline, destination, adapter, sampler).
    """
    if isinstance(config, str | Path):
        config = load_pipeline_config(config)

    # create source
    if config.source is None:
        source = None
    else:
        _, source = cast(tuple[str, Source], create_component_from_config(config.source))

    # create transformers
    transformers: list[tuple[str, Transformer] | Transformer] = []
    for transformer_config in config.transformers:
        name, transformer = cast(tuple[str, Transformer], create_component_from_config(transformer_config))

        if name:
            transformers.append((name, transformer))
        else:
            transformers.append(transformer)

    # create destination
    _, destination = cast(tuple[str, Destination[Any]], create_component_from_config(config.destination))

    # create adapter
    adapter = create_adapter_from_config(config.adapter)

    # create sampler
    sampler = create_sampler_from_config(config.sampler)

    return source, Pipeline(transformers), destination, adapter, sampler
