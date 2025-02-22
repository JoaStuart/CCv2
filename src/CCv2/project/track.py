from typing import Any
import librosa
import numpy as np

import constants


class AudioTrack:
    def __init__(self, path: str) -> None:
        self._path = path
        self._vol: float = 1

        self._data: np.ndarray[Any, Any] = librosa.load(path, sr=constants.SAMPLE_RATE, mono=False)[0]  # type: ignore

    @property
    def track(self) -> np.ndarray[Any, Any]:
        return self._data

    @property
    def length(self) -> int:
        return self.track.shape[1]

    @property
    def volume(self) -> float:
        return self._vol

    @volume.setter
    def volume(self, target: float) -> None:
        self._vol = target
