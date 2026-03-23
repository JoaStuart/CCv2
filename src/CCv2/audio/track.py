import os
import cv2
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
        self._path = path
        self._name: str = os.path.splitext(os.path.basename(path))[0].capitalize()

        logger.debug(f"Loading audio file `{path}`...")
        from scipy.io.wavfile import read

        self._sr: int
        self._data: AudioRaw
        self._sr, self._data = read(path)  # type: ignore
        assert self._sr == constants.SAMPLE_RATE

        self._waveform = self.to_waveform_uri()
        logger.debug("Finished loading audio")

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def track(self) -> AudioRaw:
        return self._data

    @property
    def length(self) -> float:
        return self.track.shape[0] / self._sr

    @property
    def volume(self) -> float:
        return self._vol

    @property
    def waveform(self) -> str:
        return self._waveform

    @volume.setter
    def volume(self, target: float) -> None:
        self._vol = target

    def to_waveform_uri(self) -> str:
        seconds = self._data.shape[0] / self._sr
        w_sec = 150
        width = int(w_sec * seconds)
        height = 60

        iinfo = np.iinfo(self._data.dtype)
        img = np.zeros((height, width, 4), dtype=np.uint8)

        for w in range(width):
            sample_start = min(int((w / w_sec) * self._sr), self._data.shape[0])
            sample_end = min(int(((w + 1) / w_sec) * self._sr), self._data.shape[0])
            samples = self._data[sample_start:sample_end, :]

            def normalize(num) -> float:
                num += iinfo.min
                return num / (iinfo.max - iinfo.min)

            normal_max = normalize(int(samples.max()))
            normal_min = normalize(int(samples.min()))

            img_max = int(normal_max * height)
            img_min = int(normal_min * height)
            if img_min == img_max:
                img_max += 1

            img[img_min:img_max, w, :] = (0, 0, 0, 255)

        success, buffer = cv2.imencode(".png", img)
        assert success

        return make_data_uri(buffer.tobytes(), "image/png")
