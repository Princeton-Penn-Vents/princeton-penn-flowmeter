#!/usr/bin/env python3
from __future__ import annotations

from zeroconf import ServiceInfo, Zeroconf
from ifaddr import get_adapters
from processor.collector import MAC_STR
from typing import Iterator
import threading
import ipaddress


def get_ip() -> Iterator[str]:
    for iface in get_adapters():
        if iface.ips and iface.name not in ["lo", "lo0"]:
            yield from (addr.ip for addr in iface.ips if addr.is_IPv4)


class Broadcast:
    def __init__(self, service: str) -> None:
        self.zeroconf = Zeroconf()
        self.info = ServiceInfo(
            "_http._tcp.local.",
            "Princeton Open Vent Monitor._http._tcp.local.",
            addresses=[ipaddress.ip_address(ip).packed for ip in get_ip()],
            port=8100,
            properties={
                "type": "povm",
                "mac_addr": MAC_STR,
                "service": service,
                "v": "1",
            },
        )

    def __enter__(self) -> Broadcast:
        self.zeroconf.register_service(self.info)
        return self

    def __exit__(self, *exc) -> None:
        # Unregister service for whatever reason
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()


if __name__ == "__main__":
    with Broadcast("broadcast"):
        forever = threading.Event()
        forever.wait()
