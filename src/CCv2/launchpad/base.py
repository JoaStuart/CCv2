import abc
import re
import time
from typing import Any, Callable, Optional
import rtmidi

from ..utils.daemon_thread import DaemonThread
from ..launchpad.route import LaunchpadRouter
from ..lighting.lightmap import Lightmap
from .. import logger
from ..ptypes import int2
from ..utils.color import col
from ..utils.ui_property import UiProperty


def register_adapters() -> None:
    from . import lps
    from . import mk2
    from . import mk3pro
    from . import lppro


class Launchpad(abc.ABC):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    CC_ON = 0xB0

    LIGHT_STATIC = 0x00
    LIGHT_FLASH = 0x01
    LIGHT_PULSE = 0x02

    INPUTS: "list[LaunchpadIn]" = []
    OUTPUTS: "list[LaunchpadOut]" = []

    _MIDI_IN = rtmidi.MidiIn()  # type: ignore
    _MIDI_OUT = rtmidi.MidiOut()  # type: ignore

    PAGE: UiProperty[int] = UiProperty(0)

    @staticmethod
    @abc.abstractmethod
    def name_re() -> str:
        pass

    @staticmethod
    def get_by_name_in(name: str) -> "Optional[type[LaunchpadIn]]":
        register_adapters()

        for t in LaunchpadIn.__subclasses__():
            if len(re.findall(t.name_re(), name)) > 0:
                return t
        return None

    @staticmethod
    def get_by_name_out(name: str) -> "Optional[type[LaunchpadOut]]":
        register_adapters()

        for t in LaunchpadOut.__subclasses__():
            if len(re.findall(t.name_re(), name)) > 0:
                return t
        return None

    @staticmethod
    def open_all() -> None:
        for i in range(Launchpad._MIDI_IN.get_port_count()):
            Launchpad.load_input(i)

        for i in range(Launchpad._MIDI_OUT.get_port_count()):
            Launchpad.load_output(i)

        LaunchpadChecker()  # Start the checker

    @staticmethod
    def load_input(index: int) -> None:
        name = Launchpad._MIDI_IN.get_port_name(index)

        tpe = Launchpad.get_by_name_in(name)
        if tpe:
            Launchpad.INPUTS.append(tpe(index, name))
            logger.debug("Opened %s as %s", name, tpe.__name__)
            Launchpad._MIDI_IN = rtmidi.MidiIn()  # type: ignore

    @staticmethod
    def load_output(index: int) -> None:
        name = Launchpad._MIDI_IN.get_port_name(index)

        tpe = Launchpad.get_by_name_out(name)
        if tpe:
            Launchpad.OUTPUTS.append(lp := tpe(index, name))
            lp.send_welcome_messages()
            logger.debug("Opened %s as %s", name, tpe.__name__)
            Launchpad._MIDI_OUT = rtmidi.MidiOut()  # type: ignore

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
            if (m := o.clear_message()) is not None:
                o.send(m)

            else:
                for d in data:
                    o.send_light(Launchpad.NOTE_ON, d, col(0, 0, 0))

    @staticmethod
    def simulate_down(x: int, y: int) -> None:
        for i in Launchpad.INPUTS:
            i.callback.note_on(x, y, 0xFF)

    @staticmethod
    def simulate_up(x: int, y: int) -> None:
        for i in Launchpad.INPUTS:
            i.callback.note_off(x, y)

    @property
    def offx(self) -> int:
        return getattr(self, "_offx", 0)

    @offx.setter
    def offx(self, val: int) -> None:
        self._offx = val

    @property
    def offy(self) -> int:
        return getattr(self, "_offy", 0)

    @offy.setter
    def offy(self, val: int) -> None:
        self._offy = val

    @abc.abstractmethod
    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        pass

    def special_xy_to_midi(
        self, pos: int2, mode: int, color: int
    ) -> Optional[list[int]]:
        return None

    @abc.abstractmethod
    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        pass

    @abc.abstractmethod
    def lightmap(self) -> str:
        pass

    @abc.abstractmethod
    def check_bounds(self, pos: int2) -> bool:
        pass

    @abc.abstractmethod
    def clear_button(self) -> int2:
        pass

    def _welcome_messages(self) -> list[list[int]]:
        return []

    def clear_message(self) -> Optional[list[int]]:
        return None


class LaunchpadChecker(DaemonThread):
    def __init__(self) -> None:
        self._last_in_count: int = Launchpad._MIDI_IN.get_port_count()
        self._last_out_count: int = Launchpad._MIDI_OUT.get_port_count()

        super().__init__("MidiChecker")

    def thread_loop(self) -> None:
        time.sleep(0.5)

        self._last_in_count = self._check(
            self._last_in_count,
            Launchpad._MIDI_IN,
            Launchpad.INPUTS,
            Launchpad.load_input,
        )
        self._last_out_count = self._check(
            self._last_out_count,
            Launchpad._MIDI_OUT,
            Launchpad.OUTPUTS,
            Launchpad.load_output,
        )

    def _check(
        self,
        last_ports: int,
        midi: Any,
        active: list[LaunchpadIn] | list[LaunchpadOut],
        load: Callable[[int], None],
    ) -> int:
        new_ports: int = midi.get_port_count()

        if new_ports > last_ports:
            for i in range(new_ports):
                if not self._has_port_named(midi.get_port_name(i), active):
                    load(i)

        elif new_ports < last_ports:
            port_names: list[str] = midi.get_ports()

            for i in range(len(active) - 1, -1, -1):
                a = active[i]
                if a.midiname not in port_names:
                    a.close()
                    active.pop(i)

        return new_ports

    def _has_port_named(
        self, name: str, active: list[LaunchpadIn] | list[LaunchpadOut]
    ) -> bool:
        for a in active:
            if a.midiname == name:
                return True

        return False


class LaunchpadIn(Launchpad):

    def __init__(self, index: int, midiname: str) -> None:
        self._midiname = midiname
        self._in = Launchpad._MIDI_IN.open_port(index)
        self._callback: LaunchpadRouter = LaunchpadRouter(self)

        self._in.set_callback(self._on_data)

    @property
    def midiname(self) -> str:
        return self._midiname

    @property
    def callback(self) -> LaunchpadRouter:
        return self._callback

    @callback.setter
    def callback(self, callback: LaunchpadRouter) -> None:
        self._callback = callback

    def _on_data(self, event: tuple[list[int], float], *args) -> None:
        data = event[0]
        assert isinstance(data, list)

        self._callback.route(*data)

    def close(self) -> None:
        self._in.close_port()


class LaunchpadOut(Launchpad):

    def __init__(self, index: int, midiname: str) -> None:
        self._midiname = midiname
        self._out = Launchpad._MIDI_OUT.open_port(index)
        self._lightmap = Lightmap.MAPS[self.lightmap()]

    @property
    def midiname(self) -> str:
        return self._midiname

    def send(self, data: list[int]) -> None:
        try:
            self._out.send_message(data)
        except:
            logger.error("Could not send midi message %s", str(data))

    def send_welcome_messages(self) -> None:
        for m in self._welcome_messages():
            self.send(m)

        from ..lighting.lightmanager import LightManager

        kf = LightManager().get_active_view()
        for pos, col in kf.items():
            self.send_light(Launchpad.NOTE_ON, pos, col)

    def send_light(self, cmd: int, pos: int2, color: col) -> None:
        pos = (pos[0] - self.offx, pos[1] - self.offy)

        if not self.check_bounds(pos):
            return

        vel = self._lightmap.closest(color)
        special = self.special_xy_to_midi(pos, cmd, vel)
        if special is not None:
            self.send(special)
            return

        note, cmd = self.xy_to_midi(pos, cmd)
        self.send([cmd, note, vel])

    def close(self) -> None:
        self._out.close_port()
