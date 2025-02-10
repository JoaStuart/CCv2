import logging
import sys

_LOG = logging.getLogger()


def init(verbose: bool) -> None:
    lvl = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s :: %(funcName)s<@>%(threadName)s [%(levelname)-1.1s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(lvl)
    console_handler.setFormatter(formatter)

    _LOG.setLevel(lvl)
    _LOG.addHandler(console_handler)


debug = _LOG.debug
info = _LOG.info
warning = _LOG.warning
error = _LOG.error
exception = _LOG.exception
