from functools import lru_cache
import time
from pathlib import Path

import logging

logger = logging.getLogger("povm")


@lru_cache(1)
def get_mac_addr() -> str:
    """
    Blocks until eth0 is up (linux) or returns all 0's on macOS (en0).
    """

    if not Path("/sys").exists():
        return "00:00:00:00:00:00"
    while True:
        try:
            mac = open("/sys/class/net/eth0/address").read().strip()
            logger.info(f"MAC Addr: {mac}")
            return mac
        except IOError:
            time.sleep(1)
