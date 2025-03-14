import os
import threading
import time
from typing import Callable, Optional
import numpy as np
import soundfile as sf
import pygame  # type: ignore # Pylance cannot resolve self-compiled pygame
import pygame.mixer as mx  # type: ignore

import constants
from daemon_thread import DaemonThread
from ptypes import AudioRaw
from singleton import singleton

mx.init(
    frequency=constants.SAMPLE_RATE,
    channels=2,
    size=constants.SAMPLE_DEPTH_PG,
    allowedchanges=pygame.AUDIO_ALLOW_ANY_CHANGE,
)
mx.set_num_channels(constants.OUT_CHANNELS)


@singleton
class AudioRouter(DaemonThread):
    def __init__(self) -> None:
        self._playing_audio: list[
            tuple[mx.Channel, float, Callable[[float], None], float]
        ] = []
        self._data_event: threading.Event = threading.Event()

        super().__init__("AudioTicker")

    def thread_loop(self) -> None:
        if len(self._playing_audio) == 0:
            self._data_event.wait()
            self._data_event.clear()

        to_remove: list[int] = []

        paud = self._playing_audio.copy()
        for i, aud in enumerate(paud):
            t = time.time()
            ch, start, callback, duration = aud

            duration -= t - start

            if duration > 0:
                if callback:
                    callback(t - start)

                if len(paud) != len(self._playing_audio):
                    return
                self._playing_audio[i] = (ch, t, callback, duration)
            else:
                if len(paud) != len(self._playing_audio):
                    return
                to_remove.append(i)

        to_remove.sort(reverse=True)

        for i in to_remove:
            self._playing_audio.pop(i)

        time.sleep(1 / constants.AUDIO_TICKS)

    def channel(self) -> mx.Channel:
        return mx.find_channel(force=True)

    def _sound(self, data: AudioRaw) -> mx.Sound:
        return mx.Sound(array=data)

    def play(
        self, data: AudioRaw, callback: Optional[Callable[[float], None]] = None
    ) -> mx.Channel:
        c = self.channel()
        c.play(self._sound(data))

        if callback:
            start = time.time()
            self._playing_audio.append(
                (c, start, callback, data.shape[0] / constants.SAMPLE_RATE)
            )
            self._data_event.set()

        return c

    def stop(self, channel: mx.Channel) -> None:
        channel.stop()
        target: int = -1

        for i, data in enumerate(self._playing_audio):
            if data[0] == channel:
                target = i
                break
        else:
            return

        self._playing_audio.pop(target)


audio_router = AudioRouter()
