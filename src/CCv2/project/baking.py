from typing import TYPE_CHECKING, Optional
import constants
from ptypes import AudioRaw, int2

if TYPE_CHECKING:
    from project.project import Project


class BakedProject:
    def __init__(self, root: "Project") -> None:
        self._project = root

        self._audios: dict[tuple[int, int2], AudioRaw] = self._bake_audios()

    def _bake_audios(self) -> dict[tuple[int, int2], AudioRaw]:
        audio: dict[tuple[int, int2], AudioRaw] = {}
        ts = self._project.timestamps.v

        for i, t in enumerate(ts):
            start = t.time

            if len(ts) == i + 1:
                end = self._project.max_length()
            else:
                end = ts[i + 1].time

            audio[(t.page, t.pos)] = self._project.get_segment(
                round(start * constants.SAMPLE_RATE),
                round(end * constants.SAMPLE_RATE),
            )

        return audio

    def get(self, page: int, pos: int2) -> Optional[AudioRaw]:
        return self._audios.get((page, pos), None)
