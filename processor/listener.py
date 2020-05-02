#!/usr/bin/env python3
from __future__ import annotations

from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import threading
import queue
import logging
import ipaddress
from typing import Set, Callable
from processor.config import init_logger

logger = logging.getLogger("povm")


class Listener(ServiceListener):
    def __init__(self):
        self.detected: Set[str] = set()
        self.inject: Callable[[], None] = lambda: None
        self.queue = queue.Queue()

    def _injects(self, addrs: Set[str]):
        new = addrs - self.detected
        self.detected |= addrs
        for item in new:
            self.queue.put(item)
        self.inject()

    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        addrs = self._add_if_unseen("added", zeroconf, service_type, name)
        self._injects(addrs)

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        addrs = self._add_if_unseen("updated", zeroconf, service_type, name)
        self._injects(addrs)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self._add_if_unseen("updated", zeroconf, service_type, name)

    def _add_if_unseen(
        self, status: str, zeroconf: Zeroconf, service_type: str, name: str
    ) -> Set[str]:
        if "Princeton Open Vent Monitor" in name:
            info = zeroconf.get_service_info(service_type, name)
            if not info:
                logger.info(f"Service {name} not {status}, missing info!")
                return set()

            addresses = {
                f"tcp://{ipaddress.ip_address(ip)}:{info.port}" for ip in info.addresses
            }

            macaddr = info.properties.get(b"mac_addr")
            service = info.properties.get(b"service")

            logger.info(f"Service {name} {status}: {addresses} - {macaddr} - {service}")
            return addresses

        else:
            logger.info(f"Service {name} not {status}")
            return set()


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

    @property
    def inject(self) -> Callable[[], None]:
        return self.listener.inject

    @inject.setter
    def inject(self, func: Callable[[], None]):
        self.listener.inject = func

    @property
    def queue(self) -> queue.Queue:
        return self.listener.queue


if __name__ == "__main__":
    init_logger()

    with FindBroadcasts():
        forever = threading.Event()
        forever.wait()
