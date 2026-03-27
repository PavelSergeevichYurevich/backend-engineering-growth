import logging
import sys


def setup_logging() -> None:
    """Initialize project-wide logging once at app startup."""
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    handler.setFormatter(formatter)

    root.setLevel(logging.INFO)
    root.addHandler(handler)
