"""
Pipeline runner module for executing complete data processing pipelines.
"""

from collections.abc import Iterator

from app.pipeline.adapters import Adapter, NoopAdapter
from app.pipeline.base import Pipeline
from app.pipeline.destinations.base import Destination
from app.pipeline.functions import chunk
from app.pipeline.samplers import Sampler
from app.pipeline.sources.base import Source
from app.schemas import Document
from app.types import DataItem


class PipelineRunner:
    """
    Runner for executing a complete pipeline from source to destination.

    Connects a source, an optional sampler, an adapter, a pipeline, and a destination
    into a data processing workflow.
    """

    def __init__(
        self,
        source: Source,
        pipeline: Pipeline,
        destination: Destination[Document],
        batch_size: int = 10,
        adapter: Adapter | None = None,
        sampler: Sampler | None = None,
    ) -> None:
        self.source = source
        self.pipeline = pipeline
        self.destination = destination
        self.batch_size = batch_size
        self.adapter = adapter if adapter else NoopAdapter()
        self.sampler = sampler

    def _items(self) -> Iterator[tuple[str, DataItem]]:
        if self.sampler is None:
            for item in self.source:
                yield ("all", item)
        else:
            yield from self.sampler.sample(self.source)

    def run(self) -> int:
        """
        Run the complete pipeline.

        :return: Number of items processed
        """
        processed_count = 0

        for batch in chunk(self._items(), batch_size=self.batch_size):
            if not batch:
                break

            # Convert DataItems to Documents, preserving the split tag on metadata.
            document_batch = []
            for split, item in batch:
                doc = self.adapter.adapt(item)
                meta = doc.metadata.model_dump()
                meta["split"] = split
                doc.metadata = type(doc.metadata).model_validate(meta)
                document_batch.append(doc)

            processed_items = self.pipeline.process(document_batch)

            for item in processed_items:
                self.destination.ingest(item)

            processed_count += len(batch)

        return processed_count
