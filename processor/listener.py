#!/usr/bin/env python3
from __future__ import annotations

from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import threading
import logging
import ipaddress

logger = logging.getLogger("povm")


class Listener(ServiceListener):
    def __init__(self):
        self.detected = []

    def remove_service(
        self, zeroconf: "Zeroconf", service_type: str, name: str
    ) -> None:
        info = zeroconf.get_service_info(service_type, name)
        logger.info(f"Service {name} removed")

    def update_service(
        self, zeroconf: "Zeroconf", service_type: str, name: str
    ) -> None:
        print("Update", name)
        if name == "Princeton Open Vent Monitor._http._tcp.local.":
            info = zeroconf.get_service_info(service_type, name)
            addresses = [str(ipaddress.ip_address(ip)) for ip in info.addresses]
            print(
                addresses,
                info.properties.get(b"mac_addr"),
                info.properties.get(b"service"),
            )

    def add_service(self, zeroconf: "Zeroconf", service_type: str, name: str) -> None:
        print("Add", name)
        if name == "Princeton Open Vent Monitor._http._tcp.local.":
            info = zeroconf.get_service_info(service_type, name)
            addresses = [str(ipaddress.ip_address(ip)) for ip in info.addresses]
            print(
                addresses,
                info.properties.get(b"mac_addr"),
                info.properties.get(b"service"),
            )


class FindBroadcasts:
    def __init__(self):

        self.zeroconf = Zeroconf()
        self.listener = Listener()

    def __enter__(self) -> FindBroadcasts:
        self.browser = ServiceBrowser(self.zeroconf, "_http._tcp.local.", self.listener)
        return self

    def __exit__(self, *exc) -> None:
        self.zeroconf.close()


if __name__ == "__main__":
    with FindBroadcasts():
        forever = threading.Event()
        forever.wait()
