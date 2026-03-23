import abc
import threading
import time
from typing import Optional

from ..utils.daemon_thread import DaemonThread
from ..launchpad.base import Launchpad
from ..lighting.keyframes import Keyframes
from ..ptypes import int2
from ..singleton import singleton
from ..utils.color import col

type Kf = dict[int2, col]


class KfData:
    def __init__(
        self, frame: Keyframes, duration: Optional[float] = None, offset: int2 = (0, 0)
    ) -> None:
        self.frame = frame.copy()
        if duration:
            self.frame.anim_time = duration

        self.offset = offset

        self.next_wait = self.frame.next_wait
        self.last = self.frame.last
        self.next = self.frame.next
        self.static_after = self.frame.static_after


@singleton
class LightManager(DaemonThread):
    def __init__(self) -> None:
        self._active_frames: list[tuple[KfData, threading.Event]] = []
        self._active_timers: list[tuple[float, KfData, threading.Event]] = []

        self._current_launchpad: Kf = {}
        self._static_launchpad: Kf = {}
        self._new_frame_notifier = threading.Event()
        self._receiver: list[LightReceiver] = []

        super().__init__("LightManager")

    def stop(self) -> None:
        self._active_frames.clear()
        self._active_timers.clear()
        self._current_launchpad.clear()
        self._static_launchpad.clear()

        for r in self._receiver:
            for x in range(-1, 9):
                for y in range(-1, 10):
                    r[x, y] = col(0, 0, 0)

            r.finish()

    def play_raw(
        self, kf: KfData, event: Optional[threading.Event] = None
    ) -> threading.Event:
        finish_event = event or threading.Event()

        self._active_frames.append((kf, finish_event))
        self._new_frame_notifier.set()

        return finish_event

    def play_after(
        self, t: float, kf: Keyframes, duration: float, offset: int2
    ) -> threading.Event:
        if t <= 0:
            return self.play_raw(KfData(kf, duration, offset))

        e = threading.Event()
        self._active_timers.append((time.time() + t, KfData(kf, duration, offset), e))
        self._new_frame_notifier.set()

        return e

    def play(
        self, name: str, duration: Optional[float] = None, offset: int2 = (0, 0)
    ) -> threading.Event:
        keyframes = Keyframes.FRAME_CACHE.get(name, None)
        if keyframes is None:
            sevent = threading.Event()
            sevent.set()
            return sevent

        return self.play_raw(KfData(keyframes, duration, offset))

    def _get_shortest_wait(self) -> float:
        return min([d[0].next_wait() for d in self._active_frames], default=1)

    def _get_shortest_timer(self) -> float:
        return min([d[0] - time.time() for d in self._active_timers], default=1)

    def thread_loop(self) -> None:
        if len(self._active_frames) == 0 and len(self._active_timers) == 0:
            self._new_frame_notifier.wait()
            self._new_frame_notifier.clear()
        else:
            wait = min(self._get_shortest_wait(), self._get_shortest_timer())
            if wait > 0:
                self._new_frame_notifier.wait(wait)
                self._new_frame_notifier.clear()

        self._handle_frame()
        self._handle_timers()

    def thread_cleanup(self) -> None:
        return self._new_frame_notifier.set()

    def _handle_timers(self) -> None:
        finished_timers: list[int] = []

        for i, t in enumerate(self._active_timers):
            if t[0] - time.time() > 0:
                continue

            finished_timers.append(i)
            self._timer_callback(*t)

        finished_timers.sort(reverse=True)

        for i in finished_timers:
            self._active_timers.pop(i)

    def _timer_callback(self, _: float, kf: KfData, ev: threading.Event) -> None:
        self.play_raw(kf, ev)

    def _draw_frames(
        self, next_screen: Kf, finished_frames: list[tuple[KfData, threading.Event]]
    ) -> None:
        for kf, end in self._active_frames:
            if kf.next_wait() > 0:
                frame = kf.last()

                if not frame:
                    continue
            else:
                frame = kf.next()

            if frame is None:
                if kf.static_after:
                    frame = kf.last()

                    if not frame:
                        continue

                    for k, v in frame.items():
                        self._static_launchpad[
                            k[0] + kf.offset[0], k[1] + kf.offset[1]
                        ] = v

                finished_frames.append((kf, end))
                end.set()
                continue

            self._draw_frame(frame, kf.offset, next_screen)

    def _handle_static(self, next_screen: Kf) -> None:
        static_remove: list[int2] = []
        for k, v in self._static_launchpad.items():
            if next_screen.get(k, None) is not None:
                static_remove.append(k)

        for r in static_remove:
            del self._static_launchpad[r]

    def _convert_xor(self, next_screen: Kf) -> Kf:
        write_buffer: Kf = {}
        for k in self._current_launchpad.keys() | next_screen.keys():
            if self._current_launchpad.get(k, 0) != next_screen.get(k, 0):
                write_buffer[k] = next_screen.get(k, col(0, 0, 0))

        return write_buffer

    def _handle_frame(self) -> None:
        next_screen: Kf = {}
        finished_frames: list[tuple[KfData, threading.Event]] = []

        self._draw_frames(next_screen, finished_frames)

        for f in finished_frames:
            self._active_frames.remove(f)

        self._handle_static(next_screen)

        next_screen |= self._static_launchpad

        write_buffer = self._convert_xor(next_screen)

        self._broadcast_buffer(write_buffer)
        self._current_launchpad = next_screen

    def _draw_frame(self, frame: Kf, offset: int2, next_screen: Kf) -> None:
        for p, v in frame.items():
            next_screen[p[0] + offset[0], p[1] + offset[1]] = v

    def add_light_receiver(self, receiver: "LightReceiver") -> None:
        self._receiver.append(receiver)

    def _broadcast_buffer(self, write_buffer: Kf) -> None:
        if len(write_buffer) == 0:
            return

        for pos, vel in write_buffer.items():
            Launchpad.broadcast_light(
                Launchpad.NOTE_ON | Launchpad.LIGHT_STATIC, pos, vel
            )

            for r in self._receiver:
                r[pos] = vel

        for r in self._receiver:
            r.finish()


class LightReceiver(abc.ABC):
    @abc.abstractmethod
    def __setitem__(self, pos: int2, c: col) -> None:
        pass

    @abc.abstractmethod
    def finish(self) -> None:
        pass
