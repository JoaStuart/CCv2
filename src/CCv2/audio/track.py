import os
import numpy as np

from ..utils.data_uri import make_data_uri

from .. import constants
from .. import logger
from ..ptypes import AudioRaw


class AudioTrack:
    def __init__(self, path: str) -> None:
        path = os.path.abspath(path)
        self._path = path
        self._vol: float = 1
        self._name: str = os.path.splitext(os.path.basename(path))[0].capitalize()

        logger.debug(f"Loading audio file `{path}`...")
        from scipy.io.wavfile import read

        self._data: AudioRaw = read(
            path,
        )[1]
        logger.debug("Finished loading audio")

    @property
    def name(self) -> str:
        return self._name

    @property
    def track(self) -> AudioRaw:
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
