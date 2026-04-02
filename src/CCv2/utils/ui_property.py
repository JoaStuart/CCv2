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

from typing import Callable


class UiProperty[_T](property):
    def __init__(self, default: _T):
        self._value = default
        self._listeners: list[Callable[[_T], None]] = []

    @property
    def v(self) -> _T:
        return self._value

    @v.setter
    def v(self, target: _T) -> None:
        self._value = target

        self.change()

    def change(self) -> None:
        for l in self._listeners:
            l(self._value)

    def add_listener(self, listener: Callable[[_T], None]) -> int:
        self._listeners.append(listener)
        return len(self._listeners) - 1

    def remove_listener(
        self, listener: Callable[[_T], None] | None = None, index: int | None = None
    ) -> None:
        if listener is not None:
            self._listeners.remove(listener)
        elif index is not None:
            self._listeners.pop(index)

    def __str__(self) -> str:
        return str(self.v)
