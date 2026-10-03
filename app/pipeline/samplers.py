"""
Stratified sampler: allocates Documents across named splits via polars-splitters.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import ClassVar

import polars as pl
from polars_splitters import split_into_train_eval
from pydantic import BaseModel, Field

from app.schemas import Document


class Sampler(ABC):
    """
    Base sampler interface. Rewrites a Document stream into split-tagged Documents.
    """

    name: ClassVar[str]
    description: ClassVar[str] = ""

    @abstractmethod
    def sample(self, source: Iterable[Document]) -> Iterator[Document]:
        """
        Consume Documents, yield Documents with split name tagged at ``metadata["split"]``.

        :param source: Iterable of Documents.
        :return: Iterator of Documents, each carrying ``metadata["split"]``.
        """
        pass


class StratifiedSampler(Sampler, BaseModel):
    """
    Stratified split across named splits (2 or 3-way), delegated to polars-splitters.
    3-way is composed of two `split_into_train_eval` calls (train peeled first,
    remainder re-proportioned).
    """

    name: ClassVar[str] = "stratified"
    description: ClassVar[str] = "Stratified split across named splits via polars-splitters."

    label_field: str = Field(description="The metadata key carrying the class label (used for stratification).")
    stratify_fields: list[str] = Field(
        default_factory=list,
        description="Additional metadata keys to include in the strata key alongside the label.",
    )
    splits: dict[str, float] = Field(
        default={"train": 0.8, "val": 0.1, "test": 0.1},
        description="Split names → proportions. Must sum to 1.0 and have 2 or 3 entries.",
    )
    shuffle: bool = Field(default=True, description="Shuffle rows before splitting.")
    seed: int = Field(default=42, description="Random seed for reproducibility.")

    def model_post_init(self, __context) -> None:  # type: ignore[no-untyped-def]
        total = sum(self.splits.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"splits must sum to 1.0, got {total}")
        if not 2 <= len(self.splits) <= 3:
            raise ValueError("splits must have 2 or 3 entries")

    def sample(self, source: Iterable[Document]) -> Iterator[Document]:
        docs = list(source)
        rows = [
            {"_idx": i, "source": d.source, **(d.metadata or {})}
            for i, d in enumerate(docs)
        ]
        df = pl.DataFrame(rows)
        stratify_by = [self.label_field, *self.stratify_fields]
        names = list(self.splits.keys())

        parts: dict[str, pl.DataFrame]
        if len(names) == 2:
            train_name, eval_name = names
            eval_rel = self.splits[eval_name]
            train_df, eval_df = split_into_train_eval(
                df, eval_rel_size=eval_rel, stratify_by=stratify_by, shuffle=self.shuffle, seed=self.seed
            )
            parts = {train_name: train_df, eval_name: eval_df}
        else:
            train_name, validation_name, test_name = names
            p_train = self.splits[train_name]
            df_rest, df_train = split_into_train_eval(
                df, eval_rel_size=p_train, stratify_by=stratify_by, shuffle=self.shuffle, seed=self.seed
            )
            p_validation_in_rest = self.splits[validation_name] / (1 - p_train)
            df_validation, df_test = split_into_train_eval(
                df_rest,
                eval_rel_size=p_validation_in_rest,
                stratify_by=stratify_by,
                shuffle=self.shuffle,
                seed=self.seed,
            )
            parts = {
                train_name: df_train,
                validation_name: df_validation,
                test_name: df_test,
            }

        for name, part_df in parts.items():
            for row in part_df.iter_rows(named=True):
                d = docs[row["_idx"]]
                d.metadata = {**(d.metadata or {}), "split": name}
                yield d
