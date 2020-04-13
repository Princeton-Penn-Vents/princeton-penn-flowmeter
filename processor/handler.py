from datetime import datetime
import http.server
import json
from urllib.parse import urlparse, parse_qs
from functools import partial


def make_handler(generator):
    return partial(Handler, generator)


class Handler(http.server.BaseHTTPRequestHandler):
    def __init__(self, generator, *args, **kwargs):
        self.generator = generator
        super().__init__(*args, **kwargs)

    def parse_url(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            d = parse_qs(parsed.query)
            return {k: int(v[0]) for k, v in d.items()}

    def do_HEAD(self):
        if self.parse_url() is None:
            self.send_response(404)
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        return True

    def do_GET(self):
        parsed_path = urlparse(self.path)
        print(self.parse_url())

        t_now = int(1000 * datetime.now().timestamp())
        d = self.generator.prepare()

        # For the simulation, returning and empty dict simulates disconnection.
        # Probably best to remove.
        if d:
            if self.do_HEAD():
                self.wfile.write(json.dumps(d).encode("ascii"))
        else:
            self.send_error(408)
