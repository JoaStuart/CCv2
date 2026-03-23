from typing import TYPE_CHECKING, Optional

from .. import constants
from ..lighting.keyframes import Keyframes
from ..ptypes import AudioRaw, int2

if TYPE_CHECKING:
    from ..project.project import Project


type PagedAudio = dict[tuple[int, int2], list[AudioRaw]]
type PagedLight = dict[
    tuple[int, int2], dict[int, list[tuple[float, Keyframes, float, int2]]]
]  # (page, (x, y)): (??, [(time, kf, duration, offset)])


class BakedProject:
    def __init__(self, root: "Project") -> None:
        self._project = root

        self._positions_audio: dict[tuple[int, int2], int] = {}
        self._positions_light: dict[tuple[int, int2], int] = {}

        self._button_indicies: dict[float, int] = {}

        self._audios: PagedAudio = self._bake_audios()
        self._lights: PagedLight = self._bake_lighting()

    def _bake_lighting(self) -> PagedLight:
        lighting: PagedLight = {}

        buttons = self._project.timestamps.v

        for l in self._project.lighting.v:
            prev_buttons = [b for b in buttons if b.time <= l.time]

            if len(prev_buttons) == 0:
                print("Non-shown light baked")
                continue  # We can ignore lights that dont get shown

            attached_key = prev_buttons[-1]
            delta = l.time - attached_key.time

            btn_idx = self._button_indicies[attached_key.time]
            existing = lighting.get((attached_key.page, attached_key.pos), {})
            btn_lights = existing.get(btn_idx, [])

            btn_lights.append(
                (delta, Keyframes.FRAME_CACHE[l.light], l.duration, l.offset)
            )

            existing[btn_idx] = btn_lights
            lighting[(attached_key.page, attached_key.pos)] = existing

        return lighting

    def _bake_audios(self) -> PagedAudio:
        audio: PagedAudio = {}
        ts = self._project.timestamps.v

        for i, t in enumerate(ts):
            start = t.time

            if len(ts) == i + 1:
                end = self._project.max_length() / constants.SAMPLE_RATE
            else:
                end = ts[i + 1].time
                if end == start:
                    if len(ts) == i + 2:
                        end = self._project.max_length() / constants.SAMPLE_RATE
                    else:
                        end = ts[i + 2].time

            pos = (t.page, t.pos)
            existing = audio.get(pos, [])

            idx = len(existing)

            segment = self._project.get_segment(
                round(start * constants.SAMPLE_RATE),
                round(end * constants.SAMPLE_RATE),
            )
            if len(segment) == 0:
                print("Start", start, "End", end, "Next", ts[i + 1].page, ts[i + 1].pos)
            existing.append(segment)

            audio[pos] = existing
            self._positions_audio[pos] = 0
            self._button_indicies[start] = idx

        return audio

    def _incr_sound(self, page: int, pos: int2) -> None:
        clips_amnt = len(self._audios.get((page, pos), []))
        current = self._positions_audio.get((page, pos), 0)

        self._positions_audio[(page, pos)] = (current + 1) % clips_amnt

    def _incr_light(self, page: int, pos: int2) -> None:
        clips_amnt = len(self._lights.get((page, pos), []))
        current = self._positions_light.get((page, pos), 0)

        self._positions_light[(page, pos)] = (current + 1) % clips_amnt

    def get_audio(self, page: int, pos: int2) -> Optional[AudioRaw]:
        clips = self._audios.get((page, pos), None)

        if clips is None:
            return None

        target = clips[self._positions_audio[(page, pos)]]

        self._incr_sound(page, pos)
        return target

    def get_light(self, page: int, pos: int2):
        lights = self._lights.get((page, pos), None)

        if lights is None:
            return None

        target = lights[self._positions_light.get((page, pos), 0)]

        self._incr_light(page, pos)
        return target
