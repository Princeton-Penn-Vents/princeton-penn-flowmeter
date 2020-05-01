from typing import Any, Iterable, Tuple, List

SUB: int
SUBSCRIBE: int
PUB: int

POLLIN: int
POLLOUT: int

class Socket:
    def setsockopt_string(self, _1: int, _2: str) -> None: ...
    def subscribe(self, _: bytes) -> None: ...
    def send_string(self, _: str) -> None: ...
    def send_json(self, _: Any) -> None: ...
    def connect(self, _: str) -> None: ...
    def disconnect(self, address: str) -> None: ...
    def bind(self, _: str) -> None: ...
    def recv_json(self) -> Any: ...
    def poll(self, timeout: float, flags: int = ...) -> int: ...
    def __enter__(self) -> Socket: ...
    def __exit__(self, *args) -> None: ...

class Context:
    def socket(self, _: int) -> Socket: ...
    def __enter__(self) -> Context: ...
    def __exit__(self, *args) -> None: ...
    def setsockopt(self, _: int, s: bytes) -> None: ...
    @classmethod
    def instance(cls) -> Context: ...

def select(
    rlist: Iterable[Socket],
    wlist: Iterable[Socket],
    xlist: Iterable[Socket],
    timeout=None,
) -> Tuple[List[Socket], List[Socket], List[Socket]]: ...
