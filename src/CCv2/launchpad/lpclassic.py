import math
import threading
import time

from ..utils.daemon_thread import DaemonThread
from ..lighting.lightmanager import LightManager
from ..ptypes import int2
from ..utils.color import col
from ..launchpad.base import Launchpad, LaunchpadIn, LaunchpadOut


class LaunchpadClassic(Launchpad):
    @staticmethod
    def name_re() -> str:
        return r"Launchpad MIDI"

    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        if mode <= self.NOTE_ON + 0xF:
            if midi >= 0x24 and midi <= 0x43:  # Left side notes
                return midi % 4, 17 - midi // 4 - 1

            if midi >= 0x44 and midi <= 0x63:  # Right side notes
                return midi % 4 + 4, 25 - midi // 4 - 1

            if midi >= 0x64 and midi <= 0x6B:  # Right side register
                return 8, midi - 0x64

        else:  # ControlChange
            if midi >= 0x5A and midi <= 0x62:
                return midi % 10 - 1, 9 - midi // 10 - 1

        if midi < 99:
            return midi % 10 - 1, 9 - midi // 10 - 1
        return midi - 104, -1

    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        x, y = xy

        if y == -1:
            return 0x68 + x, mode + self.CC_ON - self.NOTE_ON
        elif y >= 0 and y <= 7:
            if x == 8:  # Right register
                return 100 + y, mode
            elif x < 4:
                return 68 - 4 * y + (x - 4), mode
            else:
                return (96 - (4 * y)) + (x - 4), mode
        else:
            return 0, mode

    def check_bounds(self, pos: tuple[int, int]) -> bool:
        return pos[0] >= 0 and pos[0] <= 8 and pos[1] >= -1 and pos[1] <= 7

    def lightmap(self) -> str:
        return "ClassicMiniS"

    def clear_button(self) -> tuple[int, int]:
        return 0, -1

    def _welcome_messages(self) -> list[list[int]]:
        return [
            [
                0xB0,
                0x00,
                0x02,
            ],  # Change to USER1 mode
        ]


class LaunchpadClassicIn(LaunchpadClassic, LaunchpadIn):
    pass


class LaunchpadClassicUpdater(DaemonThread):
    def __init__(self, lp: LaunchpadClassicOut) -> None:
        self._lp = lp

        super().__init__("LpClassicUpdater")

    def thread_loop(self) -> None:
        wait = self._lp.next_update_at - time.time()
        if wait > 0:
            time.sleep(wait)

        self._lp.frame_finish()


class LaunchpadClassicOut(LaunchpadClassic, LaunchpadOut):

    def __init__(self, index: int, midiname: str) -> None:
        super().__init__(index, midiname)

        self._message_map: dict[int2, int] = {}
        self.next_update_at: float = 0
        self._currently_sending: threading.Event = threading.Event()

        self._update_checker = LaunchpadClassicUpdater(self)

    def send_light(self, cmd: int, pos: tuple[int, int], color: col) -> None:
        pos = (pos[0] - self.offx, pos[1] - self.offy)

        if not self.check_bounds(pos):
            return

        self._message_map[pos] = self._lightmap.closest(color)

    def _rapid_messages_needed(self) -> int:
        msg_needed = 0

        for (x, y), _ in self._message_map.items():
            n = 0

            if x == 8:
                n = math.ceil((64 + y) / 2)
            elif y == -1:
                n = math.ceil((64 + 8 + x) / 2)
            else:
                n = math.ceil((y * 8 + x + 1) / 2)

            if n > msg_needed:
                msg_needed = n

        return msg_needed

    def _rapid_to_xy(self, rapid_num: int) -> int2:
        if rapid_num < 64:
            return rapid_num % 8, rapid_num // 8
        elif rapid_num < 64 + 8:
            return 8, rapid_num - 64
        else:
            return rapid_num - 64 - 8, -1

    def _rapid_velo_at(self, xy: int2, full_frame: dict[int2, col]) -> int:
        if xy in self._message_map:
            vel = self._message_map[xy]
            del self._message_map[xy]
        else:
            vel = self._lightmap.closest(full_frame.get(xy, col(0, 0, 0)))

        return vel

    def _send_data_rapid(self) -> int:
        RAPID_UPDATE = Launchpad.NOTE_ON + 2
        rapid_num = 0

        full_frame = LightManager().get_active_view()
        full_rapid_msg = self._rapid_messages_needed()

        # Check if sending leftover lights raw would be better
        should_continue = lambda: (full_rapid_msg - rapid_num // 2) < len(
            self._message_map
        )

        while len(self._message_map) > 0 and should_continue():
            self.send(
                [
                    RAPID_UPDATE,
                    self._rapid_velo_at(self._rapid_to_xy(rapid_num), full_frame),
                    self._rapid_velo_at(self._rapid_to_xy(rapid_num + 1), full_frame),
                ]
            )

            rapid_num += 2

        return rapid_num // 2

    def _send_data_raw(self) -> int:
        for xy, vel in self._message_map.items():
            note, cmd = self.xy_to_midi(xy, Launchpad.NOTE_ON)
            self.send([cmd, note, vel])

        return len(self._message_map)

    def frame_finish(self) -> None:
        if self._currently_sending.is_set() or self.next_update_at > time.time():
            return

        self._currently_sending.set()

        SEC_PER_MSG = 2.5 / 1000

        msg_rapid = self._send_data_rapid()
        msg_raw = self._send_data_raw()

        if msg_raw == 0:
            self.send([Launchpad.NOTE_ON, 0, 0])
            msg_raw = 1

        messages_used = msg_rapid + msg_raw
        self.next_update_at = time.time() + SEC_PER_MSG * messages_used

        self._message_map = {}

        self._currently_sending.clear()

    def close(self) -> None:
        self._update_checker.cleanup()
        return super().close()
