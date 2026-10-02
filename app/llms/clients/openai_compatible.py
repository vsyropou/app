from typing import Any
from urllib.parse import urljoin

import httpx

from app.llms.clients.base import BaseLLMModel
from app.llms.schemas import ChatCompletionMessage


class OpenAICompatibleModel(BaseLLMModel):
    def __init__(
        self,
        api_key: str,
        model_name: str,
        dimensions: int,
        base_url: str | None = None,
        timeout: int = 60,
        headers: dict[str, str] | None = None,
        chat_completions_path: str | None = "/v1/chat/completions",
        embeddings_path: str | None = "/v1/embeddings",
        completion_url: str | None = None,
        embedding_url: str | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/") if base_url else None
        self._chat_completions_path = chat_completions_path
        self._embeddings_path = embeddings_path
        self._completion_url = completion_url
        self._embedding_url = embedding_url
        self._model_name = model_name
        self._dimensions = dimensions
        self._timeout = timeout

        # Validate that at least one URL configuration is provided
        if not base_url and not completion_url and not embedding_url:
            raise ValueError(
                "Either base_url must be provided, or at least one of completion_url/embedding_url must be specified"
            )

        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        if headers:
            self._headers.update(headers)

    def completion(self, messages: list[ChatCompletionMessage], **kwargs: Any) -> list[str | None]:
        """
        Chat completion.

        :param messages: The list of messages to pass to the LLM.
        :return: The model's response.
        """
        # build messages
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "model": self._model_name,
            **kwargs,
        }

        with httpx.Client(timeout=self._timeout) as client:
            if self._completion_url:
                completion_url = self._completion_url
            elif self._base_url and self._chat_completions_path:
                completion_url = urljoin(self._base_url, self._chat_completions_path)
            elif self._base_url:
                completion_url = self._base_url
            else:
                raise ValueError("Either completion_url or base_url must be provided")
            response = client.post(completion_url, json=payload, headers=self._headers)

            response.raise_for_status()
            data = response.json()

            # Extract embeddings from response
            return [choice.get("message", {}).get("content") for choice in data.get("choices")]

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode the given texts to embedding vectors using OpenAI API.
        :param texts: The texts to create embeddings for.
        :return: A list of the embedding vector for each text.
        """
        if not texts:
            return []

        payload = {
            "input": texts,
            "model": self._model_name,
        }

        with httpx.Client(timeout=self._timeout) as client:
            if self._embedding_url:
                embeddings_url = self._embedding_url
            elif self._base_url and self._embeddings_path:
                embeddings_url = urljoin(self._base_url, self._embeddings_path)
            elif self._base_url:
                embeddings_url = self._base_url
            else:
                raise ValueError("Either embedding_url or base_url must be provided")
            response = client.post(embeddings_url, json=payload, headers=self._headers)

            response.raise_for_status()
            data = response.json()

            # Extract embeddings from response
            return [item["embedding"] for item in data["data"]]

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
        return self._model_name
