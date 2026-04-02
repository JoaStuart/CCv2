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

import abc
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..launchpad.base import LaunchpadIn


class LaunchpadRouter:
    def __init__(self, lp: "LaunchpadIn") -> None:
        self._lp = lp

    def route(self, cmd: int, a0: int, a1: int, *args) -> None:
        from ..launchpad.base import Launchpad

        cnc = cmd & 0xF0
        if (cnc == Launchpad.NOTE_ON or cnc == Launchpad.CC_ON) and a1 > 0:
            note = self._lp.midi_to_xy(a0, cmd)
            cx, cy = self._lp.clear_button()
            if note[0] == cx and note[1] == cy:
                LaunchpadReceiver.route_clear()

            if note[0] == 8 and note[1] >= 0:
                Launchpad.PAGE.v = note[1]

            note = (
                note[0] + self._lp.offx,
                note[1] + self._lp.offy,
            )
            self.note_on(*note, a1)
        elif cnc == Launchpad.NOTE_OFF or a1 == 0:
            self.note_off(*self._lp.midi_to_xy(a0, cmd))

    def note_on(self, x: int, y: int, _: int) -> None:
        LaunchpadReceiver.route_on(x, y)

    def note_off(self, x: int, y: int) -> None:
        LaunchpadReceiver.route_off(x, y)


class LaunchpadReceiver(abc.ABC):
    ACTIVE_RECEIVER: "Optional[LaunchpadReceiver]" = None

    @staticmethod
    def request_input(target: "LaunchpadReceiver") -> None:
        LaunchpadReceiver.ACTIVE_RECEIVER = target

    @staticmethod
    def route_click(x: int, y: int) -> None:
        from ..launchpad.base import Launchpad

        if x == 8 and y >= 0:
            Launchpad.PAGE.v = y
        if x == -1 and y == 7:
            LaunchpadReceiver.route_clear()

        LaunchpadReceiver.route_on(x, y)
        LaunchpadReceiver.route_off(x, y)

    @staticmethod
    def route_on(x: int, y: int) -> None:
        if r := LaunchpadReceiver.ACTIVE_RECEIVER:
            r.note_on(x, y)

    @staticmethod
    def route_off(x: int, y: int) -> None:
        if r := LaunchpadReceiver.ACTIVE_RECEIVER:
            r.note_off(x, y)

    @staticmethod
    def route_clear() -> None:
        if r := LaunchpadReceiver.ACTIVE_RECEIVER:
            r.btn_clear()

    @abc.abstractmethod
    def note_on(self, x: int, y: int) -> None:
        pass

    @abc.abstractmethod
    def note_off(self, x: int, y: int) -> None:
        pass

    @abc.abstractmethod
    def btn_clear(self) -> None:
        pass
