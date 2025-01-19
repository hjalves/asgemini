import argparse
import logging
import sys

from .logger import setup_logging
from .server import Server
from .utils import import_by_path

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1965


class CommandLineInterface:
    """
    Acts as the main CLI entry point for running the server.
    """

    description = "Gemini ASGI server"

    server_class = Server

    def __init__(self):
        self.parser = argparse.ArgumentParser(description=self.description)
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )
        self.parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colorized logging",
        )
        self.parser.add_argument(
            "-p",
            "--port",
            type=int,
            help="Port number to listen on (default: %(default)s)",
            default=DEFAULT_PORT,
        )
        self.parser.add_argument(
            "-b",
            "--bind",
            dest="host",
            help="The host/address to bind to (default: %(default)s)",
            default=DEFAULT_HOST,
        )
        self.parser.add_argument(
            "--certfile",
            help="The path to the SSL certificate file (default: %(default)s)",
            default="cert.pem",
        )
        self.parser.add_argument(
            "--keyfile",
            help="The path to the SSL key file (default: %(default)s)",
            default="key.pem",
        )
        self.parser.add_argument(
            "--root-path",
            dest="root_path",
            help="The setting for the ASGI root_path variable",
            default="",
        )
        self.parser.add_argument(
            "application",
            help="The application to dispatch to as path.to.module:instance.path",
        )

        self.server = None

    @classmethod
    def entrypoint(cls):
        """
        Main entrypoint for external starts.
        """
        cls().run(sys.argv[1:])

    def run(self, args):
        """
        Pass in raw argument list, it will decode them and run the server.
        """
        # Decode args
        args = self.parser.parse_args(args)

        # Set up logging
        setup_logging(verbose=args.verbose, color=not args.no_color)

        # Import the application
        sys.path.insert(0, ".")
        application = import_by_path(args.application)

        # Start the server
        logger.info("Starting server at %s:%s", args.host, args.port)
        self.server = self.server_class(
            application,
            host=args.host,
            port=args.port,
            certfile=args.certfile,
            keyfile=args.keyfile,
        )
        self.server.run()
