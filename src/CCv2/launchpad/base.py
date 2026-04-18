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
import re
import time
from typing import Any, Callable, Optional
import rtmidi

from CCv2.launchpad.midiio import MidiInput, MidiOutput

from ..utils.daemon_thread import DaemonThread
from ..launchpad.route import LaunchpadRouter
from ..lighting.lightmap import Lightmap
from .. import logger
from ..ptypes import MidiInputOpen, MidiOutputOpen, int2
from ..utils.color import col
from ..utils.ui_property import UiProperty


def register_adapters() -> None:
    from . import lps
    from . import mk2
    from . import mk3pro
    from . import lppro
    from . import lpclassic
    from . import mk3mini
    from . import mk1mini


class Launchpad(abc.ABC):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    CC_ON = 0xB0

    LIGHT_STATIC = 0x00
    LIGHT_FLASH = 0x01
    LIGHT_PULSE = 0x02

    INPUTS: "list[LaunchpadIn]" = []
    OUTPUTS: "list[LaunchpadOut]" = []

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
        for name, mopen in MidiInput.get_ports():
            Launchpad.load_input(name, mopen)

        for name, mopen in MidiOutput.get_ports():
            print(name, mopen)
            Launchpad.load_output(name, mopen)

        LaunchpadChecker()  # Start the checker

    @staticmethod
    def load_input(name: str, mopen: MidiInputOpen) -> None:
        tpe = Launchpad.get_by_name_in(name)
        if tpe:
            Launchpad.INPUTS.append(tpe(mopen, name))
            logger.debug("Opened %s as %s", name, tpe.__name__)
            Launchpad._MIDI_IN = rtmidi.MidiIn()  # type: ignore

    @staticmethod
    def load_output(name: str, mopen: MidiOutputOpen) -> None:
        tpe = Launchpad.get_by_name_out(name)
        if tpe:
            Launchpad.OUTPUTS.append(lp := tpe(mopen, name))
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
                    o.send_light(
                        Launchpad.NOTE_ON, (d[0] + o.offx, d[1] + o.offy), col(0, 0, 0)
                    )
                o.frame_finish()

    @staticmethod
    def broadcast_finish() -> None:
        for o in Launchpad.OUTPUTS:
            o.frame_finish()

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
        self._last_in_count: int = len(MidiInput.get_ports())
        self._last_out_count: int = len(MidiOutput.get_ports())

        super().__init__("MidiChecker")

    def thread_loop(self) -> None:
        time.sleep(0.5)

        self._last_in_count = self._check(
            self._last_in_count,
            MidiInput,
            Launchpad.INPUTS,
            Launchpad.load_input,
        )
        self._last_out_count = self._check(
            self._last_out_count,
            MidiOutput,
            Launchpad.OUTPUTS,
            Launchpad.load_output,
        )

    def _check(
        self,
        last_ports: int,
        midi: type[MidiInput] | type[MidiOutput],
        active: list[LaunchpadIn] | list[LaunchpadOut],
        load: Callable,
    ) -> int:
        new_ports = midi.get_ports()

        if len(new_ports) > last_ports:
            for n, mopen in new_ports:
                if not self._has_port_named(n, active):
                    load(n, mopen)

        elif len(new_ports) < last_ports:
            new_port_names = [n for n, _ in new_ports]

            for i in range(len(active) - 1, -1, -1):
                a = active[i]
                if a.midiname not in new_port_names:
                    a.close()
                    active.pop(i)

        return len(new_ports)

    def _has_port_named(
        self, name: str, active: list[LaunchpadIn] | list[LaunchpadOut]
    ) -> bool:
        for a in active:
            if a.midiname == name:
                return True

        return False


class LaunchpadIn(Launchpad):

    def __init__(self, mopen: MidiInputOpen, midiname: str) -> None:
        self._midiname = midiname
        self._in = mopen(self._on_data)
        self._callback: LaunchpadRouter = LaunchpadRouter(self)

    @property
    def midiname(self) -> str:
        return self._midiname

    @property
    def callback(self) -> LaunchpadRouter:
        return self._callback

    @callback.setter
    def callback(self, callback: LaunchpadRouter) -> None:
        self._callback = callback

    def _on_data(self, data: list[int]) -> None:
        self._callback.route(*data)

    def close(self) -> None:
        self._in.close()


class LaunchpadOut(Launchpad):

    def __init__(self, mopen: MidiOutputOpen, midiname: str) -> None:
        self._midiname = midiname
        self._out = mopen()
        self._lightmap = Lightmap.MAPS[self.lightmap()]

    @property
    def midiname(self) -> str:
        return self._midiname

    def send(self, data: list[int]) -> None:
        try:
            self._out.send(*data)
        except:
            logger.error("Could not send midi message %s", str(data))

    def send_welcome_messages(self) -> None:
        for m in self._welcome_messages():
            self.send(m)

        from ..lighting.lightmanager import LightManager

        kf = LightManager().get_active_view()
        for pos, col in kf.items():
            self.send_light(Launchpad.NOTE_ON, pos, col)

    def frame_finish(self) -> None:
        pass

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
        self._out.close()
