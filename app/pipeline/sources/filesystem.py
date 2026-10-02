from pathlib import Path
from typing import ClassVar

from pydantic import Field

from app.pipeline.sources.base import Source
from app.types import DataItem


class FilesystemSource(Source):
    """
    Source for reading files from a directory with optional glob pattern filtering.

    Iterates over files in a directory and yields file paths and content as DataItems.
    """

    name: ClassVar[str] = "file"
    description: ClassVar[str] = "Source for reading files from a directory with optional glob pattern filtering"

    directory: str = Field(
        default=".", description="Directory path to search for files. Defaults to current directory."
    )
    pattern: str = Field(default="*", description="Glob pattern to match files. Defaults to '*' (all files).")
    recursive: bool = Field(
        default=False, description="Whether to search recursively in subdirectories. Defaults to False."
    )
    read_content: bool = Field(
        default=True, description="Whether to read file content or just return file paths. Defaults to True."
    )
    encoding: str = Field(
        default="utf-8", description="File encoding to use when reading content. Defaults to 'utf-8'."
    )

    def __iter__(self) -> DataItem:
        """
        Iterates over files in the specified directory matching the glob pattern.

        :return: DataItem for each matching file
        """
        directory_path = Path(self.directory)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory}")

        # Build glob pattern
        if self.recursive:
            pattern = f"**/{self.pattern}"
        else:
            pattern = self.pattern

        # Use pathlib glob for better handling
        matching_files = directory_path.glob(pattern)

        for file_path in matching_files:
            # Skip directories
            if file_path.is_dir():
                continue

            # Make file_path relative to directory if directory is not current directory
            if self.directory != ".":
                relative_path = file_path.relative_to(directory_path)
                file_path_str = str(relative_path)
            else:
                file_path_str = str(file_path.absolute())

            data_item = {
                "file_path": file_path_str,
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
            }

            if self.read_content:
                try:
                    with open(file_path, encoding=self.encoding) as f:
                        data_item["content"] = f.read()
                except (UnicodeDecodeError, PermissionError) as e:
                    # For binary files or permission errors, include error info
                    data_item["content"] = None
                    data_item["read_error"] = str(e)

            yield data_item
