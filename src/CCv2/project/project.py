import os
import numpy as np
from typing import Any

import constants
from project.track import AudioTrack
from ptypes import int2


class Project:
    def __init__(self) -> None:
        self._tracks: list[AudioTrack] = [
            AudioTrack(os.path.join(constants.CACHE_AUDIO, "bass.wav")),
            AudioTrack(os.path.join(constants.CACHE_AUDIO, "drums.wav")),
            AudioTrack(os.path.join(constants.CACHE_AUDIO, "other.wav")),
            AudioTrack(os.path.join(constants.CACHE_AUDIO, "vocals.wav")),
        ]

        self._timestamps: list[tuple[float, int2]] = [
            (1, (0, 0)),
            (1.2, (1, 0)),
        ]

    def get_segment(self, start: int, end: int) -> np.ndarray[Any, Any]:
        return sum(
            [k.track[start:end] for k in self._tracks],
            np.zeros((end - start), dtype=np.float32),
        )

    @property
    def tracks(self) -> list[AudioTrack]:
        return self._tracks

    @property
    def buttons(self) -> list[tuple[float, int2]]:
        return self._timestamps

    def max_length(self) -> int:
        return max(t.track.shape[1] for t in self._tracks)
