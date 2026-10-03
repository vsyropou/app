import json
from typing import Any, ClassVar, Literal

import jsonschema
from jinja2 import Environment, Template, TemplateError
from pydantic import Field, field_validator, model_validator

from app.llms.factory import build_client
from app.llms.schemas import ChatCompletionMessage, OpenAICompatibleConfig, OpenAIConfig
from app.pipeline.transformers.base import Transformer
from app.schemas import Document


class LLMTransformer(Transformer):
    """
    Transformer that uses an LLM to transform the document via a prompt.
    """

    name: ClassVar[str] = "llm"
    description: ClassVar[str] = "Uses an LLM to transform the document via a prompt."

    model: OpenAIConfig | OpenAICompatibleConfig = Field(description="The model to use for the transformer.")
    system_prompt: str | None = Field(None, description="The system prompt template to use for the model.")
    user_prompt_template: str = Field(..., description="The user prompt template to use for the model.")
    response_format: dict[str, Any] | None = Field(
        None, description="Optional response format definition for responses."
    )
    temperature: float | None = Field(
        None, description="Temperature to use for generating the response", ge=0.0, le=1.0
    )
    top_p: float | None = Field(None, description="Nucleus sampling value.", ge=0.0, le=1.0)
    timeout: float | None = Field(None, description="Timeout for HTTP requests", gt=0.0)
    target: Literal["source", "metadata"] = Field(
        "source",
        description="Where to store the output: 'source' replaces document source, 'metadata' stores in metadata",
    )
    output_key: str | None = Field(
        None,
        description="The metadata key to use for storing the output when target is 'metadata'. If result is not an"
        " object and this value is empty, defaults to 'llm_output'.",
    )

    @field_validator("response_format")
    @classmethod
    def validate_response_format(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate response_format contains valid JSON schema if present."""
        if v is None:
            return v

        try:
            # Handle different response_format structures
            schema_to_validate = None

            # OpenAI structured outputs format: {"type": "json_schema", "json_schema": {"schema": {...}}}
            if isinstance(v, dict) and "json_schema" in v:
                json_schema_obj = v["json_schema"]
                if isinstance(json_schema_obj, dict) and "schema" in json_schema_obj:
                    schema_to_validate = json_schema_obj["schema"]

            # Direct schema format: {"schema": {...}}
            elif isinstance(v, dict) and "schema" in v:
                schema_to_validate = v["schema"]

            # Validate the schema if found
            if schema_to_validate is not None:
                jsonschema.Draft7Validator.check_schema(schema_to_validate)

        except (jsonschema.SchemaError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid JSON schema in response_format: {e}")

        return v

    @model_validator(mode="after")
    def setup_and_validate(self) -> "LLMTransformer":
        """Validate and setup after model creation."""
        # Handle backward compatibility: if output_key is provided but target is "source",
        # automatically set target to "metadata"

        # Build user prompt template and validate it
        try:
            # Test template rendering to catch syntax errors
            env = Environment()
            env.parse(self.user_prompt_template)
            self._template = Template(self.user_prompt_template)
        except TemplateError as e:
            raise ValueError(f"Invalid Jinja2 template in user_prompt_template: {e}")

        # Build LLM client
        self._client = build_client(self.model)
        return self

    def transform(self, document: Document) -> list[Document]:
        """
        Transform the document using an LLM with the specified prompt.

        :param document: The document to transform.
        :return: A list containing the transformed document.
        """

        # Prepare chat completion
        messages = []
        if self.system_prompt:
            messages.append(ChatCompletionMessage(role="system", content=self.system_prompt))
        messages.append(ChatCompletionMessage(role="user", content=self._template.render(document)))

        # Build model parameters, excluding None values
        model_params: dict[str, Any] = {}
        if self.response_format is not None:
            model_params["response_format"] = self.response_format
        if self.temperature is not None:
            model_params["temperature"] = self.temperature
        if self.top_p is not None:
            model_params["top_p"] = self.top_p
        if self.timeout is not None:
            model_params["timeout"] = self.timeout

        model_output = self._client.completion(messages, **model_params)
        result = model_output[0] if model_output else ""

        # Parse JSON response if response_format is specified
        if self.response_format and result:
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                # Keep original result if JSON parsing fails
                pass

        metadata = document.metadata.copy()

        if self.target == "source":
            # Output replaces document source
            source = result
        else:  # target == "metadata"
            # Output goes to metadata
            source = document.source

            # If output_key is missing/empty and result is a dict, merge the dicts
            if (not self.output_key) and isinstance(result, dict):
                # Merge result dict into metadata, preferring result values in case of conflicts
                metadata.update(result)
            else:
                # Use output_key or default to "llm_output"
                metadata_key = self.output_key if self.output_key else "llm_output"
                metadata[metadata_key] = result

        return [Document(source=source, metadata=metadata)]
