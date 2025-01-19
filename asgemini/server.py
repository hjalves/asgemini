import asyncio
import logging
import ssl
from asyncio import get_running_loop
from functools import partial

from .protocol import GeminiProtocol

log = logging.getLogger(__name__)


class Server:
    def __init__(
        self,
        application,
        host="127.0.0.1",
        port=1965,
        certfile="cert.pem",
        keyfile="key.pem",
    ):
        self.application = application
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.connections = {}

    def protocol_factory(self):
        return GeminiProtocol(self)

    async def handle(self):
        loop = get_running_loop()
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        log.debug(f"Loading certificate at {self.certfile} and key at {self.keyfile}")
        context.load_cert_chain(self.certfile, self.keyfile)
        server = await loop.create_server(
            self.protocol_factory, self.host, self.port, ssl=context
        )
        await server.serve_forever()

    def run(self):
        event_loop = asyncio.get_event_loop()
        try:
            event_loop.run_until_complete(self.handle())
        except KeyboardInterrupt:
            log.info("Exiting due to Ctrl-C/interrupt")

    def create_application(self, protocol, scope):
        input_queue = asyncio.Queue()
        log.debug(f"Creating application for {protocol}")
        application_instance = self.application(
            scope, receive=input_queue.get, send=protocol.handle_reply
        )
        self.connections[protocol] = asyncio.ensure_future(application_instance)
        self.connections[protocol].add_done_callback(
            partial(self.application_terminated, protocol)
        )
        return input_queue

    def application_terminated(self, protocol, future):
        log.debug(f"Application terminated for {protocol}")
        try:
            future.result()
        except Exception as e:
            log.exception("Application error: %s", e)
            protocol.error(50, "Internal Server Error")
        del self.connections[protocol]
