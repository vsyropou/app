"""
Pipeline runner module for executing complete data processing pipelines.
"""

from app.pipeline.adapters import Adapter, NoopAdapter
from app.pipeline.base import Pipeline
from app.pipeline.destinations.base import Destination
from app.pipeline.functions import chunk
from app.pipeline.samplers import Sampler
from app.pipeline.sources.base import Source
from app.schemas import Document


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

    def run(self) -> int:
        """
        Run the complete pipeline. The sampler (if any) runs post-transform, over the full
        processed stream, so strata see cleaned text.

        :return: Number of items processed
        """
        all_docs: list[Document] = []
        for batch in chunk(iter(self.source), batch_size=self.batch_size):
            if not batch:
                break
            documents = [self.adapter.adapt(item) for item in batch]
            all_docs.extend(self.pipeline.process(documents))

        sampled = self.sampler.sample(all_docs) if self.sampler else iter(all_docs)
        processed_count = 0
        for doc in sampled:
            self.destination.ingest(doc)
            processed_count += 1

        return processed_count
