from typing import Any

from sentence_transformers import SentenceTransformer

from app.llms.clients.base import BaseLLMModel
from app.llms.schemas import ChatCompletionMessage


class HuggingfaceEmbeddingsProvider(BaseLLMModel):
    """
    Enables interfacing with embeddings.
    """

    def __init__(
        self, model_name: str, model_kwargs: dict[str, Any] | None = None, encode_kwargs: dict[str, Any] | None = None
    ):
        self._model_name = model_name
        self._model_kwargs = model_kwargs or {}
        self._encode_kwargs = encode_kwargs or {}
        self._model: SentenceTransformer = SentenceTransformer(self._model_name, **self._model_kwargs)

    def completion(self, messages: list[ChatCompletionMessage], **kwargs: Any) -> list[str | None]:
        raise ValueError("Not supported for huggingface models")

    def encode(self, texts: list[str]) -> list[list[float]]:
        """
        Encode the given texts to embedding vectors.

        :param texts: The texts to create embeddings for.
        :return: A list of the embedding vector for each text.
        """
        clean_texts = [x.replace("\n", " ") for x in texts]
        embeddings = self._model.encode(clean_texts, **self._encode_kwargs)
        return embeddings.tolist()  # type: ignore[no-any-return]

    @property
    def dimensions(self) -> int:
        """
        Returns the number of dimensions of the embedding model.
        :return: The number of dimensions of the embedding model.
        """
        dims = self._model.get_sentence_embedding_dimension()
        if not dims:
            raise RuntimeError(f"Couldn't determine dimensions for model {self._model}")
        return dims

    @property
    def model_name(self) -> str:
        return self._model_name
