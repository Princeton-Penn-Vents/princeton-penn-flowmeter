from datetime import datetime
import http.server
import json
from urllib.parse import urlparse, parse_qs
from functools import partial
from typing import Tuple, Dict, Union, Optional, Any
from processor.collector import Collector


class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, generator: Collector, *args, **kwargs):
        self.generator = generator
        super().__init__(*args, **kwargs)

    def parse_url(self) -> Optional[Dict[str, Any]]:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            d = parse_qs(parsed.query)
            return {k: int(v[0]) for k, v in d.items()}
        else:
            return None

    def do_HEAD(self) -> bool:
        if self.parse_url() is None:
            self.send_response(404)
            return False
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        return True

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)

        t_now = int(1000 * datetime.now().timestamp())
        d = self.generator.prepare()

        # For the simulation, returning and empty dict simulates disconnection.
        # Probably best to remove.
        if d:
            if self.do_HEAD():
                self.wfile.write(json.dumps(d).encode("ascii"))
        else:
            self.send_error(408)


# The Any is for the PsuedoGenerator
def serve(server_address: Tuple[str, int], generator: Union[Collector, Any]):
    """
    Run with server_address = ("0.0.0.0", 8100)
    """

    with http.server.ThreadingHTTPServer(
        server_address, partial(Handler, generator)
    ) as httpd:
        httpd.serve_forever()
