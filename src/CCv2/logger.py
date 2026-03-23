import logging
import sys

_LOG = logging.getLogger()


def init(verbose: bool) -> None:
    """Initialize the logger

    Args:
        verbose (bool): Whether or not to output debug logging
    """

    global print

    lvl = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        "%(funcName)s<@>%(threadName)s :: [%(levelname)-1.1s] %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(lvl)
    console_handler.setFormatter(formatter)

    _LOG.setLevel(lvl)
    _LOG.addHandler(console_handler)

    print = _LOG.info

    import jpyweb

    logging.getLogger("jPyWeb").setLevel(logging.DEBUG if verbose else logging.INFO)


debug = _LOG.debug
info = _LOG.info
warning = _LOG.warning
error = _LOG.error
exception = _LOG.exception
