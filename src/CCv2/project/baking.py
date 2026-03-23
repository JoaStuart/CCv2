from typing import TYPE_CHECKING, Optional

from .. import constants
from ..ptypes import AudioRaw, int2

if TYPE_CHECKING:
    from ..project.project import Project


type PagedAudio = dict[tuple[int, int2], list[AudioRaw]]


class BakedProject:
    def __init__(self, root: "Project") -> None:
        self._project = root

        self._positions: dict[tuple[int, int2], int] = {}
        self._audios: PagedAudio = self._bake_audios()

    def _bake_audios(self) -> PagedAudio:
        audio: PagedAudio = {}
        ts = self._project.timestamps.v

        for i, t in enumerate(ts):
            start = t.time

            if len(ts) == i + 1:
                end = self._project.max_length() / constants.SAMPLE_RATE
            else:
                end = ts[i + 1].time

            pos = (t.page, t.pos)
            existing = audio.get(pos, [])

            existing.append(
                self._project.get_segment(
                    round(start * constants.SAMPLE_RATE),
                    round(end * constants.SAMPLE_RATE),
                )
            )
            audio[pos] = existing
            self._positions[pos] = 0

        return audio

    def _incr(self, page: int, pos: int2) -> None:
        clips_amnt = len(self._audios.get((page, pos), []))
        current = self._positions[(page, pos)]

        self._positions[(page, pos)] = (current + 1) % clips_amnt

    def get(self, page: int, pos: int2) -> Optional[AudioRaw]:
        clips = self._audios.get((page, pos), None)

        if clips is None:
            return None

        target = clips[self._positions[(page, pos)]]

        self._incr(page, pos)
        return target
