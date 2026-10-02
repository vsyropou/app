"""
Pipeline library for feeding texts to a RAG service.

This module provides a flexible way to define pipelines for text processing
before feeding them to a RAG service.
"""

from app.pipeline.base import Pipeline
from app.pipeline.config import PipelineConfig, TransformerConfig, create_pipeline_from_config, load_pipeline_config
from app.pipeline.transformers.base import Transformer
from app.pipeline.transformers.cleaning import (
    LowercaseTransformer,
    RemoveStopwordsTransformer,
    RemoveUnicodeTransformer,
    TextNormalizationTransformer,
)

__all__ = [
    "Pipeline",
    "Transformer",
    "LowercaseTransformer",
    "RemoveStopwordsTransformer",
    "RemoveUnicodeTransformer",
    "TextNormalizationTransformer",
    "PipelineConfig",
    "TransformerConfig",
    "create_pipeline_from_config",
    "load_pipeline_config",
]
