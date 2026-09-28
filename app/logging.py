import json
import logging
import logging.config
import pathlib
from copy import copy
from typing import Any, Literal

import pythonjsonlogger

PWD = pathlib.Path(__file__).parent


class HypercornJSONAccessFormatter(pythonjsonlogger.json.JsonFormatter):
    def format(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        client_addr, method, full_path, http_version, status_code = recordcopy.args  # type: ignore[misc]
        recordcopy.__dict__.update(
            {
                "client_addr": client_addr,
                "method": method,
                "full_path": full_path,
                "http_version": http_version,
                "status_code": status_code,
            }
        )
        return super().format(record=recordcopy)


class HypercornJSONDefaultFormatter(pythonjsonlogger.json.JsonFormatter):
    def format(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        recordcopy.__dict__.pop("color_message", None)
        return super().format(record=recordcopy)


def initialize_logging(
    log_conf_file: Literal["logging.json", "logging.prod.json"],
) -> dict[str, Any]:
    with open(PWD / "conf" / log_conf_file) as fp:
        config: dict[str, Any] = json.load(fp)
        logging.config.dictConfig(config)
        return config
