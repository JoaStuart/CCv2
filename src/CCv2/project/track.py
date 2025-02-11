import librosa
import numpy as np


class AudioTrack:
    def __init__(self, path: str) -> None:
        self._path = path
        self._vol: float = 1

        self._data: np.ndarray = librosa.load(path, sr=44100, mono=False)[0]  # type: ignore

    @property
    def track(self) -> np.ndarray:  # type: ignore
        return self._data  # type: ignore
