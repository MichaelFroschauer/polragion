import json
from collections.abc import Iterable
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from polragion.domain.work_item import PolarionWorkItem
from polragion.settings import Settings


class JsonDataFetcher:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._file_path = Path(settings.json_data_source)

    def fetch_data(self, limit: int | None = None) -> Iterable[PolarionWorkItem]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than or equal to zero")

        if limit == 0:
            return

        raw_items = self._read_json()

        for index, raw_item in enumerate(raw_items):
            if limit is not None and index >= limit:
                break

            try:
                yield PolarionWorkItem.model_validate(raw_item)
            except ValidationError as exc:
                raise ValueError(
                    f"Invalid Polarion work item at JSON array index {index} "
                    f"in '{self._file_path}'"
                ) from exc


    def _read_json(self) -> list[dict[str, Any]]:
        if not self._file_path.exists():
            raise FileNotFoundError(f"JSON file does not exist: '{self._file_path}'")

        if not self._file_path.is_file():
            raise ValueError(f"JSON path is not a file: '{self._file_path}'")

        try:
            with self._file_path.open(mode="r", encoding="utf-8") as file:
                data = json.load(file)
        except JSONDecodeError as exc:
            raise ValueError(f"File does not contain valid JSON: "
                             f"'{self._file_path}', line {exc.lineno}, column {exc.colno}"
            ) from exc
        except OSError as exc:
            raise OSError(f"Could not read JSON file: '{self._file_path}'") from exc

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array in '{self._file_path}', got {type(data).__name__}")

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Expected a JSON object at array index {index}, got {type(item).__name__}")

        return data
