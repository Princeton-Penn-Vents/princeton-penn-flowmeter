import confuse
from pathlib import Path
import argparse
from typing import Tuple, List, Optional, Sequence, Text

DIR = Path(__file__).parent.resolve()

config = confuse.Configuration("pofm", "pofm")

# Currently we are not a library; change if we change
config.clear()

# Defaults stored here
config_default = DIR / "config_default.yaml"
config.set_file(config_default)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, formatter_class=argparse.ArgumentDefaultsHelpFormatter, **kwargs
        )

        self.add_argument(
            "--config",
            default=str(DIR.parent / "pofm.yml"),
            help="YAML configuration file",
        )

        self.add_argument(
            "--debug",
            action="store_true",
            help="Start up in debug mode (fake names, log to screen, etc)",
        )

    def _prepare(self, args):
        if args.config:
            config.set_file(args.config)

        if "debug" in args:
            config["global"]["debug"] = args.debug

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
