import abc
import json
import os
import shutil
import struct
import threading
from typing import Optional
import zipfile
import zlib
import numpy as np

import constants
from audio.track import AudioTrack
import logger
from project.baking import BakedProject
from ptypes import AudioRaw, int2
from utils.json_wrapper import Json
from utils.ui_property import UiProperty


class ProjButton:
    def __init__(self, time: float, pos: int2, page: int) -> None:
        self.time = time
        self.pos = pos
        self.page = page


class Project:
    @staticmethod
    def load(path: str) -> None:
        Project._clear()

        try:
            with zipfile.ZipFile(path, "r") as zfile:
                zfile.extractall(path=constants.CACHE)
        except RuntimeError:
            raise RuntimeError("The provided file is not a valid CCv2 cover file!")

        for v in Project.versions():
            if v.check():
                from utils.runtime import RuntimeVars

                p = v.load()
                p.load_path = path

                RuntimeVars().project = p
                return

        raise RuntimeError("The provided file is not a valid CCv2 cover file!")

    @staticmethod
    def save(path: str) -> None:
        from utils.runtime import RuntimeVars

        Project.versions()[-1].dump(RuntimeVars().project)

        # Hijack `shutil`'s copying function to always have `length=0`
        # because this just makes it faster at compressing.
        # `zipfile` uses `1024*2` here instead...
        original_copy = shutil.copyfileobj

        def new_copy(fsrc, fdst, length: int = 0) -> None:
            original_copy(fsrc, fdst, 0)

        shutil.copyfileobj = new_copy

        with zipfile.ZipFile(
            path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5
        ) as zfile:
            Project._save_dir(zfile)

        shutil.copyfileobj = original_copy

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
        return [ProjectV1()]

    @staticmethod
    def load_audio(path: str) -> list[AudioTrack]:
        return [AudioTrack(os.path.join(path, k)) for k in os.listdir(path)]

    def __init__(self) -> None:
        self.tracks: UiProperty[list[AudioTrack]] = UiProperty([])

        self.timestamps: UiProperty[list[ProjButton]] = UiProperty([])
        self.timestamps.add_listener(lambda a: a.sort(key=lambda t: t.time))

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
            out += data

        info = np.iinfo(constants.SAMPLE_DEPTH)

        return np.clip(out, info.min, info.max).astype(constants.SAMPLE_DEPTH)

    def max_length(self) -> int:
        if len(self.tracks.v) == 0:
            return 0

        return max(t.track.shape[0] for t in self.tracks.v)


class ProjectLoader(abc.ABC):
    @abc.abstractmethod
    def load(self) -> Project:
        pass

    @abc.abstractmethod
    def check(self) -> bool:
        pass

    @abc.abstractmethod
    def dump(self, proj: Project) -> None:
        pass


class ProjectV1(ProjectLoader):
    def load(self) -> Project:
        tracks = Project.load_audio(constants.CACHE_AUDIO)
        proj_descr = self._load_project_descr()

        btns: list[ProjButton] = []

        for p in range(8):
            f = os.path.join(constants.CACHE_BUTTONS, f"{p}.lpb")
            if os.path.isfile(f):
                with open(f, "rb") as file:
                    data = file.read()

                btns.extend(self._load_buttons(data, p))

        p = Project()
        p.tracks.v = tracks
        p.title = proj_descr.get_item("title", str)
        p.timestamps.v = btns
        return p

    def _pdesc(self) -> str:
        return os.path.join(constants.CACHE, "project" + constants.PDESC_EXT)

    def _load_project_descr(self) -> Json:
        try:
            with open(self._pdesc(), "r") as file:
                data = file.read()
        except Exception:
            raise RuntimeError("Could not load project description file!")

        return Json.loads(data)

    def check(self) -> bool:
        return (
            self._load_project_descr()
            .get_item("$schema", str)
            .endswith("project_v1.json")
        )

    def _create_paths(self) -> None:
        for p in [
            constants.CACHE_AUDIO,
            constants.CACHE_KEYFRAMES,
            constants.CACHE_BUTTONS,
        ]:
            os.makedirs(p, exist_ok=True)

    def dump(self, proj: Project) -> None:
        data = {
            "$schema": constants.SCHEMA_PROJECT_V1,
            "title": proj.title,
        }

        with open(self._pdesc(), "w") as file:
            file.write(json.dumps(data))

        for p in range(8):
            data = self._dump_buttons(proj, p)

            if len(data) == 0:
                continue

            with open(os.path.join(constants.CACHE_BUTTONS, f"{p}.lpb"), "wb") as file:
                file.write(data)

    def _pack_key(self, x: int, y: int) -> int:
        return ((x + 1) << 4) | (y + 1)

    def _unpack_key(self, key: int) -> tuple[int, int]:
        return (key >> 4) - 1, (key & 0xF) - 1

    def _dump_buttons(self, proj: Project, page) -> bytes:
        buff: list[bytes] = []

        ts = [t for t in proj.timestamps.v if t.page == page]

        for t in ts:
            buff.append(struct.pack("fB", (t.time, self._pack_key(*t.pos))))

        return b"".join(buff)

    def _load_buttons(self, data: bytes, page: int) -> list[ProjButton]:
        btns: list[ProjButton] = []

        for i in range(0, len(data), 5):
            time, pos = struct.unpack("fB", data[i : i + 5])

            pos = self._unpack_key(pos)

            btns.append(ProjButton(time, pos, page))

        return btns
