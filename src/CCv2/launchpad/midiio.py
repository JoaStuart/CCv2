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


class WebMidiMessage:
    OPEN = 0  # TX: R{OPEN}{I/O}{port}{name}
    CLOSE = 1  # TX: R{CLOSE}{I/O}{port}
    DATA = 2  # TX: R{DATA}{port}{data...}  |  RX: R{DATA}{port}{data...}
    CONNECT = 3  # RX: R{CONNECT}{I/O}{name}
    DISCONNECT = 4  # RX: R{DISCONNECT}{I/O}{name}

    @staticmethod
    def message_open(name: str, io: str, port: int) -> bytes:
        return b"R" + bytes([WebMidiMessage.OPEN, ord(io), port]) + name.encode()

    @staticmethod
    def message_close(port: int, io: str) -> bytes:
        return b"R" + bytes([WebMidiMessage.CLOSE, ord(io), port])

    @staticmethod
    def message_data(port: int, *data: int) -> bytes:
        return b"R" + bytes([WebMidiMessage.DATA, port, *data])

    @staticmethod
    def parse_recv(data: bytes, ws: WebSocket) -> None:
        if not data.startswith(b"R"):
            return

        if data[1] == WebMidiMessage.CONNECT:
            if data[2] == ord("I"):
                WebMidiInput.append_port(data[3:].decode(), ws)
            else:
                WebMidiOutput.append_port(data[3:].decode(), ws)

        elif data[1] == WebMidiMessage.DISCONNECT:
            if data[2] == ord("I"):
                WebMidiInput.remove_port(data[3:].decode(), ws)
            else:
                WebMidiOutput.remove_port(data[3:].decode(), ws)

        elif data[1] == WebMidiMessage.DATA:
            for i in WebMidiInput.INSTANCES:
                if i.port == data[2]:
                    i.callback(list(data[3:]))

    @staticmethod
    def remove_ws(ws: WebSocket) -> None:
        WebMidiInput.remove_ws(ws)
        WebMidiOutput.remove_ws(ws)


class WebMidiInput(MidiInput):
    PORTS: dict[int, tuple[str, WebSocket]] = {}
    INSTANCES: "list[WebMidiInput]" = []

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: p[0] for i, p in WebMidiInput.PORTS.items()}

    @staticmethod
    def append_port(name: str, ws: WebSocket) -> None:
        maxid = -1
        for i, _ in WebMidiInput.PORTS.items():
            maxid = max(i, maxid)

        newid = maxid + 1
        WebMidiInput.PORTS[newid] = (str(id(ws)) + ";" + name, ws)

    @staticmethod
    def remove_port(name: str, ws: WebSocket) -> None:
        port = None

        for i, p in WebMidiInput.PORTS.items():
            if str(id(ws)) + ";" + p[0] == name:
                port = i
                break

        if port is None:
            return

        del WebMidiInput.PORTS[port]

    @staticmethod
    def remove_ws(ws: WebSocket) -> None:
        wsid = str(id(ws)) + ";"

        keys = list(WebMidiInput.PORTS.keys())
        keys.sort(reverse=True)
        for k in keys:
            if WebMidiInput.PORTS[k][0].startswith(wsid):
                del WebMidiInput.PORTS[k]

    def __init__(self, port: int, callback: MidiCallback) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        super().__init__(port, callback)

        _, self._ws = WebMidiInput.PORTS[port]
        if self._ws.application_state == WebSocketState.CONNECTED and CHECK_WEBSRV():
            WEBSRV_AWAIT(
                self._ws.send_bytes(
                    WebMidiMessage.message_open(
                        WebMidiInput.PORTS[port][0].split(";", 1)[1],
                        "I",
                        port,
                    )
                )
            )
        WebMidiInput.INSTANCES.append(self)

    def close(self) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        if self._ws.application_state == WebSocketState.CONNECTED and CHECK_WEBSRV():
            WEBSRV_AWAIT(
                self._ws.send_bytes(WebMidiMessage.message_close(self.port, "I"))
            )
        WebMidiInput.INSTANCES.remove(self)


class WebMidiOutput(MidiOutput):
    PORTS: dict[int, tuple[str, WebSocket]] = {}

    @staticmethod
    def _ports() -> dict[int, str]:
        return {i: p[0] for i, p in WebMidiOutput.PORTS.items()}

    @staticmethod
    def append_port(name: str, ws: WebSocket) -> None:
        maxid = -1
        for i, _ in WebMidiOutput.PORTS.items():
            maxid = max(i, maxid)

        newid = maxid + 1
        WebMidiOutput.PORTS[newid] = (str(id(ws)) + ";" + name, ws)

    @staticmethod
    def remove_port(name: str, ws: WebSocket) -> None:
        port = None

        for i, p in WebMidiOutput.PORTS.items():
            if str(id(ws)) + ";" + p[0] == name:
                port = i
                break

        if port is None:
            return

        del WebMidiOutput.PORTS[port]

    @staticmethod
    def remove_ws(ws: WebSocket) -> None:
        wsid = str(id(ws)) + ";"

        keys = list(WebMidiOutput.PORTS.keys())
        keys.sort(reverse=True)
        for k in keys:
            if WebMidiOutput.PORTS[k][0].startswith(wsid):
                del WebMidiOutput.PORTS[k]

    def __init__(self, port: int) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        super().__init__(port)

        _, self._ws = WebMidiInput.PORTS[port]

        if self._ws.application_state == WebSocketState.CONNECTED and CHECK_WEBSRV():
            WEBSRV_AWAIT(
                self._ws.send_bytes(
                    WebMidiMessage.message_open(
                        WebMidiOutput.PORTS[port][0].split(";", 1)[1],
                        "O",
                        port,
                    )
                )
            )

    def send(self, *data: int) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        if self._ws.application_state == WebSocketState.CONNECTED and CHECK_WEBSRV():
            WEBSRV_AWAIT(
                self._ws.send_bytes(WebMidiMessage.message_data(self.port, *data))
            )

    def close(self) -> None:
        from ..ui.web_ui import WEBSRV_AWAIT, CHECK_WEBSRV

        if self._ws.application_state == WebSocketState.CONNECTED and CHECK_WEBSRV():
            WEBSRV_AWAIT(
                self._ws.send_bytes(WebMidiMessage.message_close(self.port, "O"))
            )
