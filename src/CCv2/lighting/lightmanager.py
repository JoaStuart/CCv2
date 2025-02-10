import threading
import time
from typing import Optional
from launchpad.base import Launchpad
from lighting.keyframes import Keyframes
from singleton import singleton

type Kf = dict[tuple[int, int], int]


@singleton
class LightManager:
    def __init__(self) -> None:
        self._active_frames: list[Optional[tuple[Keyframes, threading.Event]]] = []
        self._current_launchpad: dict[tuple[int, int], int] = {}
        self._new_frame_notifier = threading.Event()

        threading.Thread(
            target=self._lighting_thread,
            name="LightManager",
            daemon=True,
        ).start()

    def play(self, name: str) -> threading.Event:
        finish_event = threading.Event()

        keyframes = Keyframes.FRAME_CACHE.get(name, None)
        if keyframes is None:
            finish_event.set()
        else:
            data = (keyframes, finish_event)
            for i in range(len(self._active_frames)):
                if self._active_frames[i] is None:
                    self._active_frames[i] = data
                    break
            else:
                self._active_frames.append(data)
            self._new_frame_notifier.set()

        return finish_event

    def _get_shortest_wait(self) -> float:
        return min([d[0].next_wait() for d in self._active_frames if d is not None])

    def _lighting_thread(self) -> None:
        while True:
            if len([f for f in self._active_frames if f is not None]) == 0:
                self._new_frame_notifier.wait()
                self._new_frame_notifier.clear()
            else:
                wait = self._get_shortest_wait()
                if wait > 0:
                    time.sleep(wait)

            self._handle_frame()

    def _handle_frame(self) -> None:
        write_buffer: Kf = {}

        for i in range(len(self._active_frames)):
            d = self._active_frames[i]
            if d is None:
                continue

            kf, end = d
            if kf.next_wait() > 0:
                continue

            frame = kf.next()

            if frame is None:
                self._active_frames[i] = None
                end.set()
                continue

            self._draw_frame(frame, write_buffer)

        self._broadcast_buffer(write_buffer)

    def _draw_frame(self, frame: Kf, write_buffer: Kf) -> None:
        for p, v in frame.items():
            if self._current_launchpad.get(p, None) == v:
                continue

            write_buffer[p] = v

    def _broadcast_buffer(self, write_buffer: Kf) -> None:
        for pos, vel in write_buffer.items():
            Launchpad.broadcast_light(
                Launchpad.NOTE_ON | Launchpad.LIGHT_STATIC, pos, vel
            )
            # TODO:
            # - Make the Keyframes be able to set the type of light to send (STATIC, FLASHING, PULSING)
            # - Make the type of launchpad be able to select the channel for each type of light
