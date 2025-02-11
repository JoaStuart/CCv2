import abc
import re
import time
from typing import Optional
import pygame.midi as midi

from daemon_thread import DaemonThread
from launchpad.route import DefaultLaunchpadRouter, LaunchpadRouter
import logger


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

    @staticmethod
    @abc.abstractmethod
    def name_re() -> str:
        pass

    @staticmethod
    def get_by_name_in(name: str) -> "Optional[type[LaunchpadIn]]":
        from launchpad.mk3pro import LaunchpadMk3ProIn

        pad_types = [LaunchpadMk3ProIn]
        for t in pad_types:
            if re.match(t.name_re(), name):
                return t
        return None

    @staticmethod
    def get_by_name_out(name: str) -> "Optional[type[LaunchpadOut]]":
        from launchpad.mk3pro import LaunchpadMk3ProOut

        pad_types = [LaunchpadMk3ProOut]
        for t in pad_types:
            if re.match(t.name_re(), name):
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
            "Discovered MIDI device %s :: IN=%d OUT=%d", name.decode(), inp, outp
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
    def broadcast_light(cmd: int, pos: tuple[int, int], vel: int) -> None:
        for o in Launchpad.OUTPUTS:
            o.send_light(cmd, pos, vel)

    @staticmethod
    def broadcast_clear() -> None:
        data: list[tuple[int, int]] = []
        for i in range(-1, 9):
            for j in range(-1, 10):
                data.append((i, j))

        for o in Launchpad.OUTPUTS:
            for d in data:
                o.broadcast_light(Launchpad.NOTE_ON, d, 0)

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
        self._callback: LaunchpadRouter = DefaultLaunchpadRouter(self)

        super().__init__("MidiReader-%d" % index)

    @property
    def callback(self) -> LaunchpadRouter:
        return self._callback

    @callback.setter
    def callback(self, callback: LaunchpadRouter) -> None:
        self._callback = callback

    def thread_loop(self) -> None:
        messages = self._in.read(1)
        if len(messages) == 0:
            return

        data = messages[0][0]
        assert isinstance(data, list)

        self._callback.route(*data)


class LaunchpadOut(Launchpad):
    def __init__(self, index: int) -> None:
        self._out = midi.Output(index)

    def send(self, data: list[int]) -> None:
        if len(data) > 4:
            self._out.write_sys_ex(0, data)
        else:
            self._out.write([[data, 0]])

    def send_welcome_messages(self) -> None:
        for m in self._welcome_messages():
            self.send(m)

    def send_light(self, cmd: int, pos: tuple[int, int], vel: int) -> None:
        note, cmd = self.xy_to_midi(pos, cmd)
        self.send([cmd, note, vel])
