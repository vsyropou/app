from typing import Any

from openai import NOT_GIVEN, OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)

from app.llms.clients.base import BaseLLMModel
from app.llms.schemas import ChatCompletionMessage


def _convert_message(message: ChatCompletionMessage) -> ChatCompletionMessageParam:
    """Convert ChatCompletionMessage to appropriate OpenAI message param type based on role."""
    if message.role == "system":
        return ChatCompletionSystemMessageParam(role="system", content=message.content)
    elif message.role == "user":
        return ChatCompletionUserMessageParam(role="user", content=message.content)
    elif message.role == "assistant":
        return ChatCompletionAssistantMessageParam(role="assistant", content=message.content)
    elif message.role == "developer":
        return ChatCompletionDeveloperMessageParam(role="developer", content=message.content)
    elif message.role == "function":
        # Function messages require a 'name' field, but our schema doesn't have it
        # For now, create basic structure - this may need enhancement later
        return ChatCompletionFunctionMessageParam(role="function", name="unknown", content=message.content)
    elif message.role == "tool":
        # Tool messages require a 'tool_call_id' field, but our schema doesn't have it
        # For now, create basic structure - this may need enhancement later
        return ChatCompletionToolMessageParam(role="tool", tool_call_id="unknown", content=message.content)
    else:
        # This should never happen due to Literal type constraints
        raise ValueError(f"Unsupported message role: {message.role}")


class OpenAIModel(BaseLLMModel):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "text-embedding-ada-002",
        dimensions: int | None = None,
    ):
        """
        Initialize OpenAI embeddings.

        :param api_key: OpenAI API key. If None, it will use the OPENAI_API_KEY environment variable
        :param base_url: Base URL for the OpenAI API. If None, it will use the default or OPENAI_BASE_URL environment
                         variable.
        :param model: Model to use for embeddings, default is text-embedding-ada-002
        :param dimensions: Custom dimensions for the embeddings, if None, defaults to model's standard dimensions
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

        # Set default dimensions based on the model if not specified.
        self._dimensions = 1536 if model == "text-embedding-ada-002" else 3072
        # Dimensions override only for models allowing it.
        if dimensions:
            self._dimensions = dimensions

    def completion(self, messages: list[ChatCompletionMessage], **kwargs: Any) -> list[str | None]:
        """
        Chat completion.

        :param messages: The list of messages to pass to the LLM.
        :return: The model's response.
        """
        # build messages

        response = self.client.chat.completions.create(
            messages=[_convert_message(m) for m in messages], model=self._model, **kwargs
        )

        # Extract the model output from the response
        return [choice.message.content for choice in response.choices]

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode the given texts to embedding vectors using OpenAI.
        :param texts: The texts to create embeddings for.
        :return: A list of the embedding vector for each text.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self._model,
            dimensions=self._dimensions
            if self._model in ("text-embedding-3-small", "text-embedding-3-large")
            else NOT_GIVEN,
        )

        # Extract the embedding vectors from the response
        return [data.embedding for data in response.data]

    @property
    def dimensions(self) -> int:
        """
        Returns the number of dimensions of the embedding model.
        :return: The number of dimensions of the embedding model.
        """
        return self._dimensions

    @property
    def model_name(self) -> str:
        """
        Returns a user-friendly name of the model.
        :return: The name of the model.
        """
        return self._model
