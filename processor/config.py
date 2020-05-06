from __future__ import annotations

import confuse
from pathlib import Path

DIR = Path(__file__).parent.resolve()

config = confuse.Configuration("povm", "povm")

# Currently we are not a library; change if we change
config.clear()

# Defaults stored here
config_default = DIR / "config_default.yaml"
config.set_file(config_default)
