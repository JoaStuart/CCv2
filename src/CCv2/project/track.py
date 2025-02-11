from typing import Any
import librosa
import numpy as np


class AudioTrack:
    def __init__(self, path: str) -> None:
        self._path = path
        self._vol: float = 1

        self._data: np.ndarray[Any, Any] = librosa.load(path, sr=44100, mono=False)[0]  # type: ignore

    @property
    def track(self) -> np.ndarray[Any, Any]:
        return self._data

    @property
    def volume(self) -> float:
        return self._vol

    @volume.setter
    def volume(self, target: float) -> None:
        self._vol = target
