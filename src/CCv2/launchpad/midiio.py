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

from fastapi import WebSocket
from fastapi.websockets import WebSocketState
import rtmidi

from ..ptypes import MidiCallback, MidiInputOpen, MidiOutputOpen


type MidiListIn = list[tuple[str, MidiInputOpen]]
type MidiListOut = list[tuple[str, MidiOutputOpen]]


class MidiInput(abc.ABC):
    @staticmethod
    def get_ports() -> MidiListIn:
        retlist: MidiListIn = []

        for s in MidiInput.__subclasses__():
            ports = s._ports()
            for i, name in ports.items():
                retlist.append((name, lambda callback, s=s, i=i: s(i, callback)))

        return retlist

    @staticmethod
    @abc.abstractmethod
    def _ports() -> dict[int, str]:
        pass

    def __init__(self, port: int, callback: MidiCallback) -> None:
        self._port = port
        self._callback = callback

    @abc.abstractmethod
    def close(self) -> None:
        pass

    @property
    def port(self) -> int:
        return self._port

    @property
    def callback(self) -> MidiCallback:
        return self._callback


class MidiOutput(abc.ABC):

    @staticmethod
    def get_ports() -> MidiListOut:
        retlist: MidiListOut = []

        for s in MidiOutput.__subclasses__():
            ports = s._ports()
            for i, name in ports.items():
                retlist.append((name, lambda s=s, i=i: s(i)))

        return retlist

    @staticmethod
    @abc.abstractmethod
    def _ports() -> dict[int, str]:
        pass

    def __init__(self, port: int) -> None:
        self._port = port

    @property
    def port(self) -> int:
        return self._port

    @abc.abstractmethod
    def send(self, *data: int) -> None:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        pass


#
#   RtMidi implementation
#


class RtMidiInput(MidiInput):
    _MIDI_IN = rtmidi.MidiIn()  # type: ignore

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: n for i, n in enumerate(RtMidiInput._MIDI_IN.get_ports())}

    def __init__(self, port: int, callback: MidiCallback) -> None:
        super().__init__(port, callback)

        self._midi_in = RtMidiInput._MIDI_IN
        RtMidiInput._MIDI_IN = rtmidi.MidiIn()  # type: ignore

        self._midi_in.open_port(port)
        self._midi_in.set_callback(lambda ev, _: self.callback(ev[0]))

    def close(self) -> None:
        self._midi_in.close_port()


class RtMidiOutput(MidiOutput):
    _MIDI_OUT = rtmidi.MidiOut()  # type: ignore

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: n for i, n in enumerate(RtMidiOutput._MIDI_OUT.get_ports())}

    def __init__(self, port: int) -> None:
        super().__init__(port)

        self._midi_out = RtMidiOutput._MIDI_OUT
        RtMidiOutput._MIDI_OUT = rtmidi.MidiOut()  # type: ignore

        self._midi_out.open_port(port)

    def send(self, *data: int) -> None:
        self._midi_out.send_message(data)

    def close(self) -> None:
        self._midi_out.close_port()


#
#   WebMidi implementation
#


class ProtoRemidi:
    OPEN = 0  # TX: R{OPEN}{I/O}{port}{name}
    CLOSE = 1  # TX: R{CLOSE}{I/O}{port}
    DATA = 2  # TX: R{DATA}{port}{data...}  |  RX: R{DATA}{port}{data...}
    CONNECT = 3  # RX: R{CONNECT}{I/O}{name}
    DISCONNECT = 4  # RX: R{DISCONNECT}{I/O}{name}

    STATE_PREINIT = 0
    STATE_RUNNING = 1

    VERSION_SUPPORT = {
        1: 0,
    }

    @staticmethod
    def closest_supported_version(version: tuple[int, int]) -> tuple[int, int]:
        if version[0] in ProtoRemidi.VERSION_SUPPORT:
            return version[0], min(version[1], ProtoRemidi.VERSION_SUPPORT[version[0]])

        maj_list = list(ProtoRemidi.VERSION_SUPPORT.keys())
        maj_list.sort(reverse=True)

        return maj_list[0], ProtoRemidi.VERSION_SUPPORT[maj_list[0]]

    def message_open(self, name: str, io: str, port: int) -> bytes:
        return bytes([self._prefix, ProtoRemidi.OPEN, ord(io), port]) + name.encode()

    def message_close(self, port: int, io: str) -> bytes:
        return bytes([self._prefix, ProtoRemidi.CLOSE, ord(io), port])

    def message_data(self, port: int, *data: int) -> bytes:
        return bytes([self._prefix, ProtoRemidi.DATA, port, *data])

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws
        self._state: int = ProtoRemidi.STATE_PREINIT

        self._prefix: int  # Assigned during STATE_PREINIT
        self._version: tuple[int, int]  # Assigned during STATE_PREINIT

    @property
    def state(self) -> int:
        return self._state

    def send(self, data: bytes) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        if CHECK_WEBSRV():
            WEBSRV_AWAIT(self._ws.send_bytes(data))

    def parse(self, data: bytes) -> None:
        if self.state == ProtoRemidi.STATE_PREINIT:
            self._parse_state_preinit(data)
        elif self.state == ProtoRemidi.STATE_RUNNING:
            self._parse_state_running(data)

    def _parse_state_preinit(self, data: bytes) -> None:
        if not data.startswith(b"REMIDI"):
            return

        self._version = (data[6], data[7])
        self._prefix = data[8]

        support_ver, support_subver = self.closest_supported_version(self._version)
        self.send(b"REMIDI" + bytes([support_ver, support_subver]))

        if self._version == (support_ver, support_subver):
            self._state = ProtoRemidi.STATE_RUNNING

    def _parse_state_running(self, data: bytes) -> None:
        if len(data) < 1 or data[0] != self._prefix:
            return

        if data[1] == ProtoRemidi.CONNECT:
            if data[2] == ord("I"):
                WebMidiInput.append_port(data[3:].decode(), self)
            else:
                WebMidiOutput.append_port(data[3:].decode(), self)

        elif data[1] == ProtoRemidi.DISCONNECT:
            if data[2] == ord("I"):
                WebMidiInput.remove_port(data[3:].decode(), self)
            else:
                WebMidiOutput.remove_port(data[3:].decode(), self)

        elif data[1] == ProtoRemidi.DATA:
            for i in WebMidiInput.INSTANCES:
                if i.port == data[2]:
                    i.callback(list(data[3:]))

    def close(self) -> None:
        WebMidiInput.remove_ws(self)
        WebMidiOutput.remove_ws(self)


class WebMidiInput(MidiInput):
    PORTS: dict[int, tuple[str, ProtoRemidi]] = {}
    INSTANCES: "list[WebMidiInput]" = []

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: p[0] for i, p in WebMidiInput.PORTS.items()}

    @staticmethod
    def append_port(name: str, proto: ProtoRemidi) -> None:
        maxid = -1
        for i, _ in WebMidiInput.PORTS.items():
            maxid = max(i, maxid)

        newid = maxid + 1
        WebMidiInput.PORTS[newid] = (str(id(proto)) + ";" + name, proto)

    @staticmethod
    def remove_port(name: str, proto: ProtoRemidi) -> None:
        port = None

        for i, p in WebMidiInput.PORTS.items():
            if str(id(proto)) + ";" + p[0] == name:
                port = i
                break

        if port is None:
            return

        del WebMidiInput.PORTS[port]

    @staticmethod
    def remove_ws(proto: ProtoRemidi) -> None:
        wsid = str(id(proto)) + ";"

        keys = list(WebMidiInput.PORTS.keys())
        keys.sort(reverse=True)
        for k in keys:
            if WebMidiInput.PORTS[k][0].startswith(wsid):
                del WebMidiInput.PORTS[k]

    def __init__(self, port: int, callback: MidiCallback) -> None:
        super().__init__(port, callback)

        _, self._proto = WebMidiInput.PORTS[port]
        self._proto.send(
            self._proto.message_open(
                WebMidiInput.PORTS[port][0].split(";", 1)[1],
                "I",
                port,
            )
        )
        WebMidiInput.INSTANCES.append(self)

    def close(self) -> None:
        self._proto.send(self._proto.message_close(self.port, "I"))
        WebMidiInput.INSTANCES.remove(self)


class WebMidiOutput(MidiOutput):
    PORTS: dict[int, tuple[str, ProtoRemidi]] = {}
    INSTANCES: "list[WebMidiOutput]" = []

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: p[0] for i, p in WebMidiOutput.PORTS.items()}

    @staticmethod
    def append_port(name: str, proto: ProtoRemidi) -> None:
        maxid = -1
        for i, _ in WebMidiOutput.PORTS.items():
            maxid = max(i, maxid)

        newid = maxid + 1
        WebMidiOutput.PORTS[newid] = (str(id(proto)) + ";" + name, proto)

    @staticmethod
    def remove_port(name: str, proto: ProtoRemidi) -> None:
        port = None

        for i, p in WebMidiOutput.PORTS.items():
            if str(id(proto)) + ";" + p[0] == name:
                port = i
                break

        if port is None:
            return

        del WebMidiOutput.PORTS[port]

    @staticmethod
    def remove_ws(proto: ProtoRemidi) -> None:
        wsid = str(id(proto)) + ";"

        keys = list(WebMidiOutput.PORTS.keys())
        keys.sort(reverse=True)
        for k in keys:
            if WebMidiOutput.PORTS[k][0].startswith(wsid):
                del WebMidiOutput.PORTS[k]

    def __init__(self, port: int) -> None:
        super().__init__(port)

        _, self._proto = WebMidiInput.PORTS[port]

        self._proto.send(
            self._proto.message_open(
                WebMidiOutput.PORTS[port][0].split(";", 1)[1],
                "O",
                port,
            )
        )

    def send(self, *data: int) -> None:
        self._proto.send(self._proto.message_data(self.port, *data))

    def close(self) -> None:
        self._proto.send(self._proto.message_close(self.port, "O"))
