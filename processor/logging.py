from __future__ import annotations

from pathlib import Path
from typing import TextIO, Optional
import logging

from processor.config import config

DIR = Path(__file__).parent.resolve()


def open_next(mypath: Path) -> Path:
    """
    Open the next available file
    """
    i = 0
    while True:
        name = "{n}{i:04}{s}".format(n=mypath.stem, i=i, s=mypath.suffix)
        new_file_path = mypath.with_name(name)
        if not new_file_path.exists():
            return new_file_path
        else:
            i += 1


def init_logger(logstr: Optional[str] = None) -> None:
    """
    logstr should be nurse_log/nursegui.log or similar (or None for screen only, even non-debug)
    """

    logger = logging.getLogger("povm")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S",
    )

    if logstr is None or config["global"]["debug"].get(bool):
        ch = logging.StreamHandler()
        logger.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    else:
        file_path = DIR.parent / logstr
        file_path.parent.mkdir(exist_ok=True)
        logfile_incr = open_next(file_path)
        fh = logging.FileHandler(logfile_incr)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def make_nested_logger(nested: int) -> logging.Logger:
    logger = logging.getLogger("povm")
    print("Making nested logger", nested)

    if len(logger.handlers) != 1:
        raise RuntimeError("Too many handlers")

    handler: logging.Handler = logger.handlers[0]

    nested_logger: logging.Logger = logging.getLogger(f"povm-{nested:02}")
    formatter = logging.Formatter(
        f"%(asctime)s - %(levelname)s - {nested:02} - %(message)s", "%Y-%m-%d %H:%M:%S",
    )
    nested_logger.setLevel(logger.level)

    if isinstance(handler, logging.FileHandler):
        main_path = Path(handler.baseFilename).with_suffix("")
        main_path.mkdir(exist_ok=True)
        new_path = main_path / f"{nested:02}"
        new_path.mkdir(exist_ok=True)

        fh = logging.FileHandler(new_path / f"{main_path.stem}.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        nested_logger.addHandler(fh)

    elif isinstance(handler, logging.StreamHandler):
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        nested_logger.addHandler(ch)

    else:
        raise RuntimeError(f"Logger handler {handler} is not of a known type!")

    return nested_logger
