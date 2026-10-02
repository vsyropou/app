from abc import ABCMeta, abstractmethod
from typing import Any

from app.llms.schemas import ChatCompletionMessage


class BaseLLMModel(metaclass=ABCMeta):
    """
    Base class for all different methods that convert text to embeddings.
    """

    @abstractmethod
    def completion(self, messages: list[ChatCompletionMessage], **kwargs: Any) -> list[str | None]:
        """
        Chat completion.

        :param messages: The list of messages to pass to the LLM.
        :return: The model's response.
        """
        pass

    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode the given texts to embedding vectors.
        :param texts: The texts to create embeddings for.
        :return: A list of the embedding vector for each text.
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """
        Returns the number of dimensions of the embedding model.
        :return: The number of dimensions of the embedding model.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Returns a user-friendly name of the model.
        :return: The name of the model.
        """
        pass
