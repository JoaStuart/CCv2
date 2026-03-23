import abc
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..launchpad.base import LaunchpadIn


class LaunchpadRouter:
    def __init__(self, lp: "LaunchpadIn") -> None:
        self._lp = lp

    def route(self, cmd: int, a0: int, a1: int, _: int) -> None:
        from ..launchpad.base import Launchpad

        cnc = cmd & 0xF0
        if cnc == Launchpad.NOTE_ON or cnc == Launchpad.CC_ON:
            note = self._lp.midi_to_xy(a0, cmd)

            if a1 == 0:
                self.note_off(*note)
            else:
                self.note_on(*note, a1)
        elif cnc == Launchpad.NOTE_OFF:
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
    def route_on(x: int, y: int) -> None:
        from launchpad.base import Launchpad

        if x == 8:
            Launchpad.PAGE.v = y
            return

        if r := LaunchpadReceiver.ACTIVE_RECEIVER:
            r.note_on(x, y)

    @staticmethod
    def route_off(x: int, y: int) -> None:
        if r := LaunchpadReceiver.ACTIVE_RECEIVER:
            r.note_off(x, y)

    @abc.abstractmethod
    def note_on(self, x: int, y: int) -> None:
        pass

    @abc.abstractmethod
    def note_off(self, x: int, y: int) -> None:
        pass
