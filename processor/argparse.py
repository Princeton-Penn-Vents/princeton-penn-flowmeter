from __future__ import annotations

import argparse
from typing import Tuple, List, Optional

from processor.config import config
from processor.logging import init_logger


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

    def _prepare(self, args):
        if args.config:
            config.set_file(args.config)

        if "debug" in args:
            config.set_args({"global": {"debug": args.debug}})

        init_logger(f"{self.type}_log" if self.type is not None else None)

    def parse_known_args(
        self, *pargs, **kwargs
    ) -> Tuple[argparse.Namespace, List[str]]:
        args, unparsed_args = super().parse_known_args(*pargs, **kwargs)
        self._prepare(args)

        return args, unparsed_args

    def parse_args(self, *pargs, **kwargs):
        args = super().parse_args(*pargs, **kwargs)
        self._prepare(args)

        return args
