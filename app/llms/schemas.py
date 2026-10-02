from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas import CustomModel


class EnvVar(BaseModel):
    envvar: str = Field(description="The name of the environment variable to use")


class OpenAIConfig(CustomModel):
    provider: Literal["openai"] = "openai"
    model: str = Field(description="The name of the model")
    dimensions: int | None = Field(None, description="The number of dimensions for the configured model.")
    api_key: str | EnvVar | None = Field(None, description="The API key to use on each request.")
    base_url: str | None = Field(None, description="URL to use for overriding OpenAI default URL.")


class OpenAICompatibleConfig(CustomModel):
    provider: Literal["openai-compatible"] = "openai-compatible"
    model: str = Field(description="The name of the model")
    dimensions: int = Field(description="The number of dimensions for the configured model.")
    api_key: str | EnvVar | None = Field(None, description="The API key to use on each request.")
    base_url: str | None = Field(None, description="Base URL for the OpenAI-compatible API.")
    embedding_url: str | None = Field(None, description="URL to use for embeddings.")
    completion_url: str | None = Field(None, description="URL to use for chat completion.")
    chat_completions_path: str | None = Field("/v1/chat/completions", description="Path for chat completions endpoint.")
    embeddings_path: str | None = Field("/v1/embeddings", description="Path for embeddings endpoint.")
    timeout: int = Field(60, description="Request timeout in seconds.")

    @model_validator(mode="after")
    def validate_url_configuration(self) -> "OpenAICompatibleConfig":
        """Validate that at least one URL configuration is provided"""
        if not self.base_url and not self.embedding_url and not self.completion_url:
            raise ValueError(
                "Either base_url must be provided, or at least one of completion_url/embedding_url must be specified"
            )

        return self


class HuggingfaceConfig(CustomModel):
    provider: Literal["huggingface"] = "huggingface"
    model: str = Field(description="The name of the model")
    model_kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Keyword args to pass to the sentence transformer model."
    )
    encode_kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Keyword args to pass when calling encode method."
    )


LLMConfig = OpenAIConfig | OpenAICompatibleConfig | HuggingfaceConfig


class ChatCompletionMessage(CustomModel):
    role: Literal["user", "system", "assistant", "developer", "function", "tool"]
    content: str = Field(description="The message's content")  # TODO: add support for other types of content
