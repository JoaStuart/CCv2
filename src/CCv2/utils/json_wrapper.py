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

import json
from typing import Any, TypeVar


_T = TypeVar("_T")


class Json:
    @staticmethod
    def loads(data: str | bytes | bytearray):
        return Json(json.loads(data))

    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def get(self, key: str | int) -> "Json":
        if isinstance(self._obj, dict):
            if key in self._obj:
                return Json(self._obj[key])
            raise RuntimeError(f"Key {key} not found!")
        elif isinstance(self._obj, list):
            if isinstance(key, int):
                return Json(self._obj[key])
            raise RuntimeError(f"A list can only be indexed with an `int`, not {key}")

        raise RuntimeError("This thing is an item!")

    def item(self, expected: type[_T]) -> _T:
        if not isinstance(self._obj, expected):
            raise RuntimeError(f"{self._obj} is not {expected}!")

        return self._obj

    def get_item(self, key: str, expected: type[_T]) -> _T:
        return self.get(key).item(expected)
