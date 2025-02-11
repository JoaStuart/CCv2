import numpy as np
from typing import Any

from project.track import AudioTrack


class Project:
    def __init__(self) -> None:
        self._tracks: list[AudioTrack] = []

    def get_segment(self, start: int, end: int) -> np.ndarray[Any, Any]:
        return sum(
            [k.track[start:end] for k in self._tracks],
            np.zeros((end - start), dtype=np.float32),
        )
