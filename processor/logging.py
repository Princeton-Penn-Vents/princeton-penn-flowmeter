from __future__ import annotations

from pathlib import Path
from typing import TextIO
import logging

from processor.config import config

DIR = Path(__file__).parent.resolve()


def open_next(mypath: Path) -> TextIO:
    """
    Open the next available file
    """
    i = 0
    while True:
        try:
            name = "{n}{i:04}{s}".format(n=mypath.stem, i=i, s=mypath.suffix)
            new_file_path = mypath.with_name(name)
            return open(new_file_path, "x")
        except FileExistsError:
            i += 1


def init_logger(logstr: str = None) -> None:
    """
    logstr should be nurse_log/nursegui.log or similar (or None for screen only, even non-debug)
    """

    logger = logging.getLogger("povm")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if logstr is None or config["global"]["debug"].get(bool):
        ch = logging.StreamHandler()
        logger.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    else:
        file_path = DIR.parent / logstr
        file_path.parent.mkdir(exist_ok=True)
        logfile_incr = file_path  # Only (over)written when no numbers left
        for i in range(100_000):
            logfile_incr = file_path.with_name(
                f"{file_path.stem}{i:05}{file_path.suffix}"
            )
            if not logfile_incr.exists():
                break

        fh = logging.FileHandler(logfile_incr.resolve())
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
