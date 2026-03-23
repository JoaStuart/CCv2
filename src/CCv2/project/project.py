import json
import os
from typing import TYPE_CHECKING, Any, Optional
import zipfile
import numpy as np

from .. import constants
from ..audio.track import AudioTrack
from .. import logger
from ..project.baking import BakedProject
from ..ptypes import AudioRaw, int2
from ..utils.json_wrapper import Json
from ..utils.ui_property import UiProperty
from ..lighting.keyframes import Keyframes

if TYPE_CHECKING:
    from .loader import ProjectLoader


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

        try:
            Launchpad.pause_read()
            logger.debug("Clearing cache")
            Project._clear()

            try:
                with zipfile.ZipFile(path, "r") as zfile:
                    zfile.extractall(path=constants.CACHE)
            except RuntimeError:
                raise RuntimeError("The provided file is not a valid CCv2 cover file!")

            for v in Project.versions():
                if v.check():
                    p = v.load()
                    p.load_path = path

                    Project.CURRENT_PROJECT.v = p
                    Keyframes.load()
                    return

            raise RuntimeError("The provided file is not a valid CCv2 cover file!")
        finally:
            Launchpad.resume_read()

    @staticmethod
    def save(path: str) -> None:
        from ..launchpad.base import Launchpad

        Launchpad.pause_read()

        Project.versions()[-1].dump(Project.CURRENT_PROJECT.v)

        with zipfile.ZipFile(
            path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5
        ) as zfile:
            Project._save_dir(zfile)

        Launchpad.resume_read()

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
    def versions() -> "list[ProjectLoader]":
        from .loader import ProjectV1

        return [ProjectV1()]

    @staticmethod
    def load_audio(path: str) -> list[AudioTrack]:
        return [AudioTrack(os.path.join(path, k)) for k in os.listdir(path)]

    @staticmethod
    def _dispatch_bake(*args) -> None:
        Project.CURRENT_PROJECT.v.bake()

    def __init__(self) -> None:
        self.tracks: UiProperty[list[AudioTrack]] = UiProperty([])

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
        out = np.zeros((end - start, 2), dtype=np.float32)

        for k in self.tracks.v:
            data = k.track[start:end, :]

            pad_amount = end - start - len(data)
            data = np.pad(
                data, ((0, pad_amount), (0, 0)), mode="constant", constant_values=0
            )
            out += data * k.volume

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
        if len(self.tracks.v) == 0:
            return 0

        return max(t.track.shape[0] for t in self.tracks.v)


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
