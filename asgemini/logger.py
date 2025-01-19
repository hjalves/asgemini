import logging
import sys


class PrettyFormatter(logging.Formatter):
    # colors
    RED = "\x1b[31;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    BLUE = "\x1b[34;20m"
    MAGENTA = "\x1b[35;20m"
    CYAN = "\x1b[36;20m"
    WHITE = "\x1b[37;20m"
    GREY = "\x1b[38;20m"
    DARK_GREY = "\x1b[38;5;240m"
    # styles
    NORMAL = "\x1b[22m"
    BOLD = "\x1b[1m"
    RESET = "\x1b[0m"

    COLOR_MAP = {
        logging.DEBUG: CYAN,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: MAGENTA,
    }

    def format(self, record):
        record.color = self.COLOR_MAP.get(record.levelno, "")
        record.normal = self.NORMAL
        record.bold = self.BOLD
        record.reset = self.RESET
        record.dark_grey = self.DARK_GREY
        return super().format(record)


def setup_logging(verbose: bool = False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logging.captureWarnings(True)

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(
        PrettyFormatter(
            fmt=(
                "%(color)s%(asctime)s.%(msecs)03d %(bold)s[%(levelname)1.1s] "
                "%(normal)s(%(threadName)s) %(name)s%(reset)s: %(message)s "
                "%(dark_grey)s(%(filename)s:%(lineno)d)%(reset)s"
            ),
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(console_handler)
