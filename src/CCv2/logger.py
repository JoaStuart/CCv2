# Copyright (C) 2026 JoaStuart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
