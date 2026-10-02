"""
Pipeline runner module for executing complete data processing pipelines.
"""

from app.pipeline.adapters import Adapter, NoopAdapter
from app.pipeline.base import Pipeline
from app.pipeline.destinations.base import Destination
from app.pipeline.functions import chunk
from app.pipeline.sources.base import Source
from app.schemas import Document


class PipelineRunner:
    """
    Runner for executing a complete pipeline from source to destination.

    This class connects a source, a pipeline of transformers, and a destination
    to create a complete data processing workflow.
    """

    def __init__(
        self,
        source: Source,
        pipeline: Pipeline,
        destination: Destination[Document],
        batch_size: int = 10,
        adapter: Adapter | None = None,
    ) -> None:
        """
        Initialize a pipeline runner.

        :param source: The data source to read items from
        :param pipeline: The processing pipeline to transform items
        :param destination: The destination to store processed items
        :param batch_size: Number of items to process in each batch (default: 10)
        :param adapter: The adapter to use for converting data items to documents.
        """
        self.source = source
        self.pipeline = pipeline
        self.destination = destination
        self.batch_size = batch_size
        self.adapter = adapter if adapter else NoopAdapter()

    def run(self) -> int:
        """
        Run the complete pipeline.

        :return: Number of items processed
        """
        processed_count = 0

        # Process items in batches to avoid memory issues with large datasets
        for batch in chunk(iter(self.source), batch_size=self.batch_size):
            if not batch:
                break  # No more items to process

            # Convert DataItems to Documents
            document_batch = [self.adapter.adapt(item) for item in batch]

            # Process the batch through the pipeline
            processed_items = self.pipeline.process(document_batch)

            # Store the processed items in the destination
            for item in processed_items:
                self.destination.ingest(item)

            # Update the processed count
            processed_count += len(batch)

        return processed_count
