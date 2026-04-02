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

import base64
import mimetypes
from typing import Optional, overload


@overload
def make_data_uri(data: str) -> str:
    """Makes a data URI from a file

    Args:
        data (str): The path to the file to convert

    Returns:
        str: The finished data uri
    """
    ...


@overload
def make_data_uri(data: bytes, mime: str) -> str:
    """Makes a data URI from raw data

    Args:
        data (bytes): The raw data to encode
        mime (str): The mime type of the data

    Returns:
        str: The finished data uri
    """
    ...


def make_data_uri(data: str | bytes, mime: Optional[str] = None) -> str:
    if isinstance(data, str):
        mime = mimetypes.guess_file_type(data)[0]

        with open(data, "rb") as rf:
            data = rf.read()

    assert mime is not None

    return "data:" + mime + ";base64," + base64.b64encode(data).decode()
