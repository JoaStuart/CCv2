import abc
import threading
from daemon_thread import DaemonThread
from launchpad.base import Launchpad
from lighting.keyframes import Keyframes
from ptypes import int2
from singleton import singleton
from utils.color import col

type Kf = dict[int2, col]


@singleton
class LightManager(DaemonThread):
    def __init__(self) -> None:
        self._active_frames: list[tuple[Keyframes, threading.Event]] = []
        self._current_launchpad: Kf = {}
        self._static_launchpad: Kf = {}
        self._new_frame_notifier = threading.Event()
        self._receiver: list[LightReceiver] = []

        super().__init__("LightManager")

    def static(self, x: int, y: int, c: col) -> None:
        self._static_launchpad[(x, y)] = c

    def play_raw(self, kf: Keyframes) -> threading.Event:
        finish_event = threading.Event()

        self._active_frames.append((kf, finish_event))
        self._new_frame_notifier.set()

        return finish_event

    def play(self, name: str) -> threading.Event:
        keyframes = Keyframes.FRAME_CACHE.get(name, None)
        if keyframes is None:
            sevent = threading.Event()
            sevent.set()
            return sevent

        return self.play_raw(keyframes)

    def _get_shortest_wait(self) -> float:
        return min([d[0].next_wait() for d in self._active_frames])

    def thread_loop(self) -> None:
        if len(self._active_frames) == 0:
            self._new_frame_notifier.clear()
            self._new_frame_notifier.wait()
        else:
            wait = self._get_shortest_wait()
            if wait > 0:
                self._new_frame_notifier.wait(wait)

        self._handle_frame()

    def _handle_frame(self) -> None:
        next_screen: Kf = {}
        finished_frames: list[tuple[Keyframes, threading.Event]] = []

        for kf, end in self._active_frames:
            if kf.next_wait() > 0:
                frame = kf.last()

                if not frame:
                    print("No last frame")
                    continue
            else:
                frame = kf.next()

            if frame is None:
                finished_frames.append((kf, end))
                end.set()
                continue

            self._draw_frame(frame, next_screen)

        for f in finished_frames:
            self._active_frames.remove(f)

        write_buffer: Kf = {}
        for k in self._current_launchpad.keys() | next_screen.keys():
            if self._current_launchpad.get(k, 0) != next_screen.get(k, 0):
                write_buffer[k] = next_screen.get(k, col(0, 0, 0))

        self._broadcast_buffer(write_buffer)
        self._current_launchpad = next_screen

    def _draw_frame(self, frame: Kf, next_screen: Kf) -> None:
        for p, v in frame.items():
            next_screen[p] = v

    def add_light_receiver(self, receiver: "LightReceiver") -> None:
        self._receiver.append(receiver)

    def _broadcast_buffer(self, write_buffer: Kf) -> None:
        for pos, vel in write_buffer.items():
            Launchpad.broadcast_light(
                Launchpad.NOTE_ON | Launchpad.LIGHT_STATIC, pos, vel
            )

            for r in self._receiver:
                r[pos] = vel

            # TODO:
            # - Make the Keyframes be able to set the type of light to send (STATIC, FLASHING, PULSING)
            # - Make the type of launchpad be able to select the channel for each type of light


class LightReceiver(abc.ABC):
    @abc.abstractmethod
    def __setitem__(self, pos: int2, c: col) -> None:
        pass
