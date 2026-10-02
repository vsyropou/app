import os
from logging import getLogger

from app.llms.clients.base import BaseLLMModel
from app.llms.clients.huggingface import HuggingfaceEmbeddingsProvider
from app.llms.clients.openai import OpenAIModel
from app.llms.clients.openai_compatible import OpenAICompatibleModel
from app.llms.schemas import EnvVar, HuggingfaceConfig, LLMConfig, OpenAICompatibleConfig, OpenAIConfig

logger = getLogger(__name__)


def build_client(config: LLMConfig) -> BaseLLMModel:
    """
    Creates a new model client using the provided configuration.
    :param config: The configuration to use for building the environment.
    :return: The instance of the LLM client.
    :raises ValueError: If the configuration contains invalid or incompatible embedding settings.
    """
    logger.info("Initializing encoder")
    if isinstance(config, HuggingfaceConfig):
        # Initialize HuggingFace embeddings
        return HuggingfaceEmbeddingsProvider(
            model_name=config.model, model_kwargs=config.model_kwargs, encode_kwargs=config.encode_kwargs
        )

    elif isinstance(config, OpenAIConfig):
        # Resolve an API key if it's an environment variable
        api_key = config.api_key
        if isinstance(api_key, EnvVar):
            api_key = os.environ.get(api_key.envvar)

        return OpenAIModel(api_key=api_key, base_url=config.base_url, model=config.model, dimensions=config.dimensions)
    elif isinstance(config, OpenAICompatibleConfig):
        # For OpenAI-compatible APIs, resolve API key if it's an environment variable
        api_key = config.api_key
        if isinstance(api_key, EnvVar):
            api_key = os.environ.get(api_key.envvar)

        return OpenAICompatibleModel(
            api_key=api_key or "",  # API key is required for compatible providers
            model_name=config.model,
            dimensions=config.dimensions,
            base_url=config.base_url,
            timeout=config.timeout,
            chat_completions_path=config.chat_completions_path,
            embeddings_path=config.embeddings_path,
            completion_url=config.completion_url,
            embedding_url=config.embedding_url,
        )

    # If we reach here, the provider is not supported
    raise ValueError(f"Unsupported embedding provider: {config.provider}")
