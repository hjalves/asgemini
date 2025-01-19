import logging
from asyncio import Protocol
from urllib.parse import urlparse

log = logging.getLogger(__name__)

MAX_REQUEST_SIZE = 1026  # 1024 + 2 for CRLF


class GeminiProtocol(Protocol):
    def __init__(self, server):
        self.server = server
        self.task = None
        self.application_queue = None
        self.transport = None
        self.peername = None
        self.scope = None
        self._response_started = False

    def __repr__(self):
        return f"<GeminiProtocol {self.peername}>"

    def connection_made(self, transport) -> None:
        self.transport = transport
        self.peername = transport.get_extra_info("peername")

    def data_received(self, data):
        if len(data) > MAX_REQUEST_SIZE:
            return self.error(59, "Request too large")
        crlf_pos = data.find(b"\r\n")
        if crlf_pos < 0:
            return self.error(59, "Bad Request")
        request = data[:crlf_pos].decode("utf-8")
        url = urlparse(request)
        if not url.scheme:
            self.error(59, "Bad Request")
        elif url.scheme != "gemini":
            self.error(53, "Proxy Request Refused")
        else:
            self.process_request(url)

    def error(self, code: int, msg: str) -> None:
        log.warning(f"{self.peername[0]}:{self.peername[1]}: {code} {msg}")
        self.transport.write(f"{code} {msg}\r\n".encode("utf-8"))
        self.finish()

    def finish(self):
        self.transport.close()
        self.transport = None
        self.send_disconnect()

    def send_disconnect(self):
        if self.application_queue:
            self.application_queue.put_nowait({"type": "gemini.disconnect"})

    def process_request(self, url):
        log.debug(f"{self.peername[0]}:{self.peername[1]}: {url.geturl()}")
        self.scope = {
            "type": "gemini",
            "url": url.geturl(),
            "scheme": url.scheme,
            "netloc": url.netloc,
            "path": url.path,
            "query": url.query,
            "root_path": "",
            "client": self.peername,
        }
        self.application_queue = self.server.create_application(self, self.scope)

    async def handle_reply(self, message):
        """Callback to handle messages from the application"""

        if not self.transport:  # Connection closed
            return

        if "type" not in message:
            raise ValueError("Message has no type defined")

        if message["type"] == "gemini.response.start":
            if self._response_started:
                raise ValueError("Response already started")
            self._response_started = True
            status = message["status"]
            header = message["header"]
            self.transport.write(f"{status} {header}\r\n".encode("utf-8"))
            url = self.scope["url"]
            log.info(
                f"{self.peername[0]}:{self.peername[1]}: {url} -> {status} {header}"
            )

        elif message["type"] == "gemini.response.body":
            if not self._response_started:
                raise ValueError("Response not yet started")
            body = message["body"]
            self.transport.write(body)
            if not message.get("more_body", False):
                self.finish()

        else:
            raise ValueError(f"Unknown message type: {message['type']}")
