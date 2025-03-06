import os
from typing import Any
import librosa
import numpy as np

import constants
import logger
from ptypes import AudioRaw


class AudioTrack:
    def __init__(self, path: str) -> None:
        path = os.path.abspath(path)
        self._path = path
        self._vol: float = 1

        logger.debug(f"Loading audio file `{path}`...")
        data: AudioRaw = librosa.load(
            path,
            sr=constants.SAMPLE_RATE,
            mono=False,
            res_type="kaiser_fast",
        )[0]
        logger.debug("Finished loading audio")

        info = np.iinfo(constants.SAMPLE_DEPTH)
        self._data = (data * info.max).astype(constants.SAMPLE_DEPTH).T.copy()

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
