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

import threading

from ..utils.color import col

STATE_SESSION = 0
STATE_USER = 1

COLOR_DIMGREEN = col.hex(0x002200)
COLOR_GREEN = col.hex(0x003E00)


class LaunchpadUI:
    INSTANCE: LaunchpadUI

    @staticmethod
    def note_on(x: int, y: int, finx: int, finy: int, vel: int) -> None:
        LaunchpadUI.INSTANCE._input.note_on(x, y, finx, finy, vel)

    @staticmethod
    def note_off(x: int, y: int, finx: int, finy: int) -> None:
        LaunchpadUI.INSTANCE._input.note_off(x, y, finx, finy)

    @staticmethod
    def note_clear() -> None:
        LaunchpadUI.INSTANCE._input.note_clear()

    @staticmethod
    def state_session() -> None:
        LaunchpadUI.INSTANCE.state = STATE_SESSION
        LaunchpadUI.statechange()

    @staticmethod
    def statechange() -> None:
        LaunchpadUI.INSTANCE._output.statechange()

    def __init__(self) -> None:
        self.state = STATE_USER
        self._input = LaunchpadUIInput(self)
        self._output = LaunchpadUIOutput(self)


class LaunchpadUIInput:
    def __init__(self, parent: LaunchpadUI) -> None:
        self._parent = parent

    def note_on(self, x: int, y: int, finx: int, finy: int, _vel: int) -> None:
        from ..launchpad.route import LaunchpadReceiver

        LaunchpadReceiver.route_on(finx, finy)

    def note_off(self, x: int, y: int, finx: int, finy: int) -> None:
        from ..launchpad.route import LaunchpadReceiver

        LaunchpadReceiver.route_off(finx, finy)

    def note_clear(self) -> None:
        from ..launchpad.route import LaunchpadReceiver

        LaunchpadReceiver.route_clear()


class LaunchpadUIOutput:
    def __init__(self, parent: LaunchpadUI) -> None:
        self._parent = parent
        self._uievent = threading.Event()

    def statechange(self) -> None:
        from ..lighting.lightmanager import DRAW_KF, DRAW_ALL, LightManager
        from ..utils import animations

        self._uievent.set()
        self._uievent = threading.Event()

        if self.isstate(STATE_USER):
            LightManager().draw_mask = DRAW_KF
            return

        LightManager().draw_mask = DRAW_ALL
        if self.isstate(STATE_USER):
            return  # Draw no session buttons

        animations.persistent(
            (
                "__button_session"
                if self.isstate(STATE_SESSION)
                else "__button_session_off"
            ),
            event=self._uievent,
        )

        animations.persistent(
            ("__button_user" if self.isstate(STATE_USER) else "__button_user_off"),
            event=self._uievent,
        )

    def isstate(self, state: int) -> bool:
        return self._parent.state == state


LaunchpadUI.INSTANCE = LaunchpadUI()
