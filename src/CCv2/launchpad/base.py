import abc
import re
import threading
import time
from typing import Optional
import pygame.midi as midi

from ..utils.daemon_thread import DaemonThread
from ..launchpad.route import LaunchpadRouter
from ..lighting.lightmap import Lightmap
from .. import logger
from ..ptypes import int2
from ..utils.color import col
from ..utils.ui_property import UiProperty


midi.init()


class Launchpad(abc.ABC):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    CC_ON = 0xB0

    LIGHT_STATIC = 0x00
    LIGHT_FLASH = 0x01
    LIGHT_PULSE = 0x02

    INPUTS: "list[LaunchpadIn]" = []
    OUTPUTS: "list[LaunchpadOut]" = []

    UNPAUSE_READ: threading.Event = threading.Event()

    PAGE: UiProperty[int] = UiProperty(0)

    @staticmethod
    @abc.abstractmethod
    def name_re() -> str:
        pass

    @staticmethod
    def pause_read() -> None:
        Launchpad.UNPAUSE_READ.clear()

    @staticmethod
    def resume_read() -> None:
        Launchpad.UNPAUSE_READ.set()

    @staticmethod
    def get_by_name_in(name: str) -> "Optional[type[LaunchpadIn]]":
        from ..launchpad.mk3pro import LaunchpadMk3ProIn

        pad_types = [LaunchpadMk3ProIn]
        for t in pad_types:
            if len(re.findall(t.name_re(), name)) > 0:
                return t
        return None

    @staticmethod
    def get_by_name_out(name: str) -> "Optional[type[LaunchpadOut]]":
        from ..launchpad.mk3pro import LaunchpadMk3ProOut

        pad_types = [LaunchpadMk3ProOut]
        for t in pad_types:
            if len(re.findall(t.name_re(), name)) > 0:
                return t
        return None

    @staticmethod
    def open_all() -> None:
        for i in range(midi.get_count()):
            Launchpad.load(i)

        LaunchpadChecker()  # Start the checker

    @staticmethod
    def load(index: int) -> None:
        _, name, inp, outp, _ = midi.get_device_info(index)
        logger.debug(
            "Discovered MIDI device '%s' :: %s%s",
            name.decode(),
            "IN" if inp > 0 else "",
            "OUT" if outp > 0 else "",
        )

        if inp == 1:
            tpe = Launchpad.get_by_name_in(name.decode())
            if tpe:
                Launchpad.INPUTS.append(tpe(index))
                logger.debug("Opened %s as %s", name.decode(), tpe.__name__)

        if outp == 1:
            tpe = Launchpad.get_by_name_out(name.decode())
            if tpe:
                Launchpad.OUTPUTS.append(lp := tpe(index))
                lp.send_welcome_messages()
                logger.debug("Opened %s as %s", name.decode(), tpe.__name__)

    @staticmethod
    def broadcast_light(cmd: int, pos: int2, color: col) -> None:
        for o in Launchpad.OUTPUTS:
            o.send_light(cmd, pos, color)

    @staticmethod
    def broadcast_clear() -> None:
        data: list[tuple[int, int]] = []
        for i in range(-1, 9):
            for j in range(-1, 10):
                data.append((i, j))

        for o in Launchpad.OUTPUTS:
            for d in data:
                o.broadcast_light(Launchpad.NOTE_ON, d, col(0, 0, 0))

    @staticmethod
    def simulate_down(x: int, y: int) -> None:
        for i in Launchpad.INPUTS:
            i.callback.note_on(x, y, 0xFF)

    @staticmethod
    def simulate_up(x: int, y: int) -> None:
        for i in Launchpad.INPUTS:
            i.callback.note_off(x, y)

    @abc.abstractmethod
    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        pass

    @abc.abstractmethod
    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        pass

    @abc.abstractmethod
    def lightmap(self) -> str:
        pass

    def _welcome_messages(self) -> list[list[int]]:
        return []


class LaunchpadChecker(DaemonThread):
    def __init__(self) -> None:
        self._last_count = midi.get_count()

        super().__init__("MidiChecker")

    def thread_loop(self) -> None:
        time.sleep(0.5)
        new_count = midi.get_count()
        if new_count > self._last_count:
            for i in range(self._last_count, new_count):
                Launchpad.load(i)

            self._last_count = new_count


class LaunchpadIn(Launchpad, DaemonThread):
    def __init__(self, index: int) -> None:
        self._in = midi.Input(index)
        self._callback: LaunchpadRouter = LaunchpadRouter(self)

        super().__init__("MidiReader-%d" % index)

    @property
    def callback(self) -> LaunchpadRouter:
        return self._callback

    @callback.setter
    def callback(self, callback: LaunchpadRouter) -> None:
        self._callback = callback

    def thread_loop(self) -> None:
        Launchpad.UNPAUSE_READ.wait()

        try:
            messages = self._in.read(1)
            if len(messages) == 0:
                return

            data = messages[0][0]
            assert isinstance(data, list)

            self._callback.route(*data)
        except RuntimeError:
            self._running = False
            return


class LaunchpadOut(Launchpad):
    def __init__(self, index: int) -> None:
        self._out = midi.Output(index)
        self._lightmap = Lightmap.MAPS[self.lightmap()]

    def send(self, data: list[int]) -> None:
        if len(data) > 4:
            self._out.write_sys_ex(0, data)
        else:
            self._out.write([[data, 0]])

    def send_welcome_messages(self) -> None:
        for m in self._welcome_messages():
            self.send(m)

    def send_light(self, cmd: int, pos: int2, color: col) -> None:
        note, cmd = self.xy_to_midi(pos, cmd)
        self.send([cmd, note, self._lightmap.vel(color)])
