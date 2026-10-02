import itertools
from collections.abc import Generator, Iterator, Sequence
from typing import Any


def chunk(iterable: Iterator[Any], batch_size: int = 10) -> Generator[Sequence[Any]]:
    """
    Convert iterable to a generator of batches.

    :param iterable: Any iterable.
    :param batch_size: Number of items in each batch.

    :return: Batches of the iterable, each of size batch_size (except possibly the last one).
    """
    if batch_size <= 0:
        raise ValueError("batch size must be > 0")

    iterator = iter(iterable)
    while batch := list(itertools.islice(iterator, batch_size)):
        if not batch:
            break
        yield batch
