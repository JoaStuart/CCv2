# Copyright (C) 2026 JoaStuart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os
from typing import Any, Optional
import zipfile
import numpy as np

from ..utils.versioning import VersionLoader
from .. import constants
from ..audio.track import AudioTrack
from .. import logger
from ..project.baking import BakedProject
from ..ptypes import AudioRaw, int2
from ..utils.json_wrapper import Json
from ..utils.ui_property import UiProperty
from ..lighting.keyframes import Keyframes


class ProjButton:
    def __init__(self, time: float, pos: int2, page: int) -> None:
        self.time = time
        self.pos = pos
        self.page = page


class ProjLight:

    def __init__(
        self, light: str, time: float, duration: Optional[float], offset: int2 = (0, 0)
    ) -> None:
        self.light = light
        self.time = time
        self.duration = (
            duration if duration is not None else Keyframes.FRAME_CACHE[light].anim_time
        )
        self.offset = offset


class Project:
    CURRENT_PROJECT: "UiProperty[Project]"

    @staticmethod
    def load(path: str) -> None:
        from ..launchpad.base import Launchpad

        logger.debug("Clearing cache")
        Project._clear()

        try:
            with zipfile.ZipFile(path, "r") as zfile:
                zfile.extractall(path=constants.CACHE)

            p = VersionLoader.load_best(Project, b"")
            p.load_path = path

            Project.CURRENT_PROJECT.v = p
            Keyframes.load()
            return

        except RuntimeError:
            raise RuntimeError("The provided file is not a valid CCv2 cover file!")

    @staticmethod
    def save(path: str) -> None:
        VersionLoader.dump_best(Project, Project.CURRENT_PROJECT.v)

        with zipfile.ZipFile(
            path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5
        ) as zfile:
            Project._save_dir(zfile)

    @staticmethod
    def _save_dir(
        zfile: zipfile.ZipFile, root: str = constants.CACHE, arcname: str = ""
    ) -> None:
        if len(arcname) > 0:
            zfile.mkdir(arcname)

        for f in os.listdir(root):
            af = os.path.join(root, f)

            if os.path.isfile(af):
                logger.debug(f"Compressing {f}...")
                zfile.write(af, arcname + f)
            else:
                logger.debug(f"Iterating {f}...")
                Project._save_dir(zfile, af, arcname + f + "/")

    @staticmethod
    def clear() -> None:
        os.makedirs(constants.CACHE, exist_ok=True)
        Project._clear()

        for d in [
            constants.CACHE_AUDIO,
            constants.CACHE_KEYFRAMES,
            constants.CACHE_PAGES,
        ]:
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def _clear(root: str = constants.CACHE) -> None:
        for f in os.listdir(root):
            af = os.path.join(root, f)

            if os.path.isfile(af):
                os.remove(af)
            else:
                Project._clear(af)
                os.removedirs(af)

    @staticmethod
    def load_audio(path: Optional[str]) -> Optional[AudioTrack]:
        if path is not None:
            return AudioTrack(os.path.join(constants.CACHE_AUDIO, path))

        auddir = os.listdir(constants.CACHE_AUDIO)
        if len(auddir) == 0:
            return None

        for a in auddir:
            if a.startswith("."):
                continue

            return AudioTrack(os.path.join(constants.CACHE_AUDIO, a))

    @staticmethod
    def _dispatch_bake(*args) -> None:
        Project.CURRENT_PROJECT.v.bake()

    def __init__(self) -> None:
        self.track: UiProperty[Optional[AudioTrack]] = UiProperty[AudioTrack | None](
            None
        )

        self.timestamps: UiProperty[list[ProjButton]] = UiProperty([])
        self.timestamps.add_listener(lambda a: a.sort(key=lambda t: t.time))
        self.timestamps.add_listener(Project._dispatch_bake)

        self.lighting: UiProperty[list[ProjLight]] = UiProperty([])
        self.lighting.add_listener(lambda a: a.sort(key=lambda t: t.time))
        self.lighting.add_listener(Project._dispatch_bake)

        self.title: str = ""
        self.load_path: Optional[str] = None

        self.baked: Optional[BakedProject] = None

    def bake(self) -> None:
        self.baked = BakedProject(self)

    def get_segment(self, start: int, end: int) -> AudioRaw:

        if self.track.v:
            out = self.track.v.track[start:end, :].astype(dtype=np.float32)
        else:
            out = np.zeros((end - start, 2), dtype=np.float32)

        info = np.iinfo(constants.SAMPLE_DEPTH)

        return self.apply_audio_fade(np.clip(out, info.min, info.max))

    def apply_audio_fade(
        self, audio: np.ndarray, fade_in_ms: float = 10, fade_out_ms: float = 10
    ) -> AudioRaw:
        fade_in_samples: int = int(constants.SAMPLE_RATE * fade_in_ms / 1000)
        fade_out_samples: int = int(constants.SAMPLE_RATE * fade_out_ms / 1000)

        fade_in = np.linspace(0.0, 1.0, fade_in_samples)[:, None]
        fade_out = np.linspace(1.0, 0.0, fade_out_samples)[:, None]

        result = audio.copy()

        result[:fade_in_samples, :] *= fade_in
        result[-fade_out_samples:, :] *= fade_out

        return result.astype(constants.SAMPLE_DEPTH)

    def max_length(self) -> int:
        if self.track.v is None:
            return 0

        return self.track.v.track.shape[0]


Project.CURRENT_PROJECT = UiProperty(Project())


class ProjDescription(Json):
    @staticmethod
    def loads(data: str | bytes | bytearray) -> "ProjDescription":
        return ProjDescription(json.loads(data))

    def __init__(self, obj: Any) -> None:
        super().__init__(obj)

        self.title: str = self.get_item("title", str)

        pages = self.get("pages")
        self.pages_buttons: list[int] = pages.get_item("buttons", list)
