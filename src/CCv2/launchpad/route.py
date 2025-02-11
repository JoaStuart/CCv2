import abc
import threading
from typing import TYPE_CHECKING
from lighting.keyframes import PersistentKeyframes

if TYPE_CHECKING:
    from launchpad.base import LaunchpadIn


class LaunchpadRouter(abc.ABC):
    def __init__(self, lp: "LaunchpadIn") -> None:
        self._lp = lp

    def route(self, cmd: int, a0: int, a1: int, a2: int) -> None:
        from launchpad.base import Launchpad

        cnc = cmd & 0xF0
        if cnc == Launchpad.NOTE_ON or cnc == Launchpad.CC_ON:
            note = self._lp.midi_to_xy(a0, cmd)

            if a1 == 0:
                self.note_off(*note)
            else:
                self.note_on(*note, a1)
        elif cnc == Launchpad.NOTE_OFF:
            self.note_off(*self._lp.midi_to_xy(a0, cmd))

    @abc.abstractmethod
    def note_on(self, x: int, y: int, vel: int) -> None:
        pass

    @abc.abstractmethod
    def note_off(self, x: int, y: int) -> None:
        pass


class DefaultLaunchpadRouter(LaunchpadRouter):
    def __init__(self, lp: "LaunchpadIn") -> None:
        super().__init__(lp)
        self._active_buttons: dict[tuple[int, int], threading.Event] = {}

    def note_on(self, x: int, y: int, vel: int) -> None:
        from lighting.lightmanager import LightManager

        self.note_off(x, y)

        e = threading.Event()
        self._active_buttons[(x, y)] = e
        kf = PersistentKeyframes(e)
        kf.append({(x, y): vel})

        LightManager().play_raw(kf)

    def note_off(self, x: int, y: int) -> None:
        ln = self._active_buttons.get((x, y), None)
        if ln:
            ln.set()
