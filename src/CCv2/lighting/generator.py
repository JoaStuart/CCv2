import threading
from launchpad.route import LaunchpadReceiver
from lighting.keyframes import PersistentKeyframes
from lighting.lightmanager import LightManager
from singleton import singleton
from utils.color import col


@singleton
class Generator(LaunchpadReceiver):
    def __init__(self) -> None:
        self._active_keys: dict[tuple[int, int], ActiveKey] = {}
        self._current_color: col = col.hex(0)

    def note_on(self, x: int, y: int) -> None:
        if (x, y) in self._active_keys:
            k = self._active_keys[(x, y)]
            k.off_event.set()

            del self._active_keys[(x, y)]
            return

        off = threading.Event()
        kf = PersistentKeyframes(off)
        kf.append({(x, y): self._current_color})
        LightManager().play_raw(kf)

        self._active_keys[(x, y)] = ActiveKey(self._current_color, off)

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)


class ActiveKey:
    def __init__(self, color: col, off_event: threading.Event) -> None:
        self.color = color
        self.off_event = off_event
