from __future__ import annotations

from pathlib import Path
import argparse
from typing import Tuple, List, Optional

from processor.config import config
from processor.logging import init_logger


DIR = Path(__file__).parent.resolve()


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, type=Optional[str], **kwargs):
        super().__init__(
            *args, formatter_class=argparse.ArgumentDefaultsHelpFormatter, **kwargs
        )

        self.add_argument(
            "--config",
            default=str(DIR.parent / "povm.yml"),
            help="YAML configuration file",
        )

        self.add_argument(
            "--debug",
            action="store_true",
            help="Start up in debug mode (log to screen)",
        )

        self.type = type

    def parse_known_args(
        self, *pargs, **kwargs
    ) -> Tuple[argparse.Namespace, List[str]]:
        # Note: This gets called by parse_args, so we don't need
        # to override both

        args, unparsed_args = super().parse_known_args(*pargs, **kwargs)

        if args.config:
            config.set_file(args.config)

        if "debug" in args:
            config.set_args({"global": {"debug": args.debug}})

        init_logger(self.type)

        return args, unparsed_args
