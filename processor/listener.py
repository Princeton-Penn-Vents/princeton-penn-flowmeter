#!/usr/bin/env python3
from __future__ import annotations

from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import threading
import logging
import ipaddress
from typing import Set
from processor.config import init_logger

logger = logging.getLogger("povm")


class Listener(ServiceListener):
    def __init__(self):
        self.detected: Set[str] = set()

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        logger.info(f"Service {name} removed")

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self._add_if_unseen("update", zeroconf, service_type, name)

    def _add_if_unseen(
        self, status: str, zeroconf: Zeroconf, service_type: str, name: str
    ):
        if name == "Princeton Open Vent Monitor._http._tcp.local.":
            info = zeroconf.get_service_info(service_type, name)
            if not info:
                logger.info(f"Not adding Service {name}, missing info!")
                return

            addresses = {
                f"tcp://{ipaddress.ip_address(ip)}:{info.port}" for ip in info.addresses
            }
            self.detected |= addresses

            macaddr = info.properties.get(b"mac_addr")
            service = info.properties.get(b"service")

            logger.info(
                f"Service {name} {status} (total {len(self.detected)}): {addresses} - {macaddr} - {service}"
            )

        else:
            logger.info(f"Not adding Service {name}")

    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self._add_if_unseen("update", zeroconf, service_type, name)


class FindBroadcasts:
    def __init__(self):

        self.zeroconf = Zeroconf()
        self.listener = Listener()

    def __enter__(self) -> FindBroadcasts:
        self.browser = ServiceBrowser(self.zeroconf, "_http._tcp.local.", self.listener)
        return self

    def __exit__(self, *exc) -> None:
        self.zeroconf.close()

    @property
    def detected(self) -> Set[str]:
        return self.listener.detected


if __name__ == "__main__":
    init_logger()

    with FindBroadcasts():
        forever = threading.Event()
        forever.wait()
