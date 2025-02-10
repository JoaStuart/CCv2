import abc
import re
import threading
import time
from typing import Callable, Optional
import pygame.midi as midi

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

        threading.Thread(
            target=Launchpad.update_loop,
            name="MidiChecker",
            daemon=True,
        ).start()

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
    def update_loop() -> None:
        last_count = midi.get_count()

        while True:
            time.sleep(0.5)
            new_count = midi.get_count()
            if new_count > last_count:
                for i in range(last_count, new_count):
                    Launchpad.load(i)

                last_count = new_count

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


type LaunchpadCallback = Callable[[int, int, int, int], None]


class LaunchpadIn(Launchpad):
    def __init__(self, index: int) -> None:
        self._in = midi.Input(index)
        self._callback = None

        threading.Thread(
            target=self._input_reader, name="MidiInput", daemon=True
        ).start()

    @property
    def callback(self) -> Optional[LaunchpadCallback]:
        return self._callback

    @callback.setter
    def callback(self, callback: LaunchpadCallback) -> None:
        self._callback = callback

    def _input_reader(self) -> None:
        while True:
            messages = self._in.read(1)
            if len(messages) == 0:
                continue

            data = messages[0][0]
            assert isinstance(data, list)

            if self._callback:
                self._callback(*data)

            # TEMP: Echo back input
            for o in Launchpad.OUTPUTS:
                o.send(data)


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
