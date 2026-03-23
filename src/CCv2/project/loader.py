import abc
import json
import os
import struct
from typing import Any

from ..lighting.keyframes import Keyframes

from .. import constants
from .. import logger
from ..project.project import ProjButton, ProjDescription, ProjLight, Project


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

        btns = self._read_buttons(proj_descr.get("pages").get_item("buttons", list))
        with open(os.path.join(constants.CACHE_PAGES, "lights.lpl"), "rb") as file:
            lights = self._load_lights(file.read())

        p = Project()
        p.tracks.v = tracks
        p.title = proj_descr.get_item("title", str)
        p.timestamps.v = btns
        p.lighting.v = lights
        return p

    def _read_buttons(self, pages: list[int]) -> list[ProjButton]:
        btns: list[ProjButton] = []

        logger.debug(f"Reading button pages {pages}")

        for p in pages:
            f = os.path.join(constants.CACHE_PAGES, f"{p}.lpb")
            if os.path.isfile(f):
                with open(f, "rb") as file:
                    data = file.read()

                btns.extend(a := self._load_buttons(data, p))

        return btns

    def _pdesc(self) -> str:
        return os.path.join(constants.CACHE, "project" + constants.PDESC_EXT)

    def _load_project_descr(self) -> ProjDescription:
        try:
            with open(self._pdesc(), "r") as file:
                data = file.read()
        except Exception:
            raise RuntimeError("Could not load project description file!")

        return ProjDescription.loads(data)

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
            constants.CACHE_PAGES,
        ]:
            os.makedirs(p, exist_ok=True)

    def dump(self, proj: Project) -> None:
        proj_data = {
            "$schema": constants.SCHEMA_PROJECT_V1,
            "title": proj.title,
            "pages": {
                "buttons": [],
                "lights": ["lights.lpl"],
            },
        }

        Keyframes.dump()
        self._dump_full_light(proj)

        for p in range(8):
            self._dump_page_btn(proj, proj_data, p)

        with open(self._pdesc(), "w") as file:
            file.write(json.dumps(proj_data))

    def _dump_page_btn(self, proj: Project, proj_data: dict[str, Any], p: int) -> None:
        data = self._dump_buttons(proj, p)

        if len(data) == 0:
            return

        proj_data["pages"]["buttons"].append(p)

        with open(os.path.join(constants.CACHE_PAGES, f"{p}.lpb"), "wb") as file:
            file.write(data)

    def _dump_full_light(self, proj: Project) -> None:
        data = self._dump_lights(proj)

        with open(os.path.join(constants.CACHE_PAGES, "lights.lpl"), "wb") as file:
            file.write(data)

    def _pack_key(self, x: int, y: int) -> int:
        return ((x + 1) << 4) | (y + 1)

    def _unpack_key(self, key: int) -> tuple[int, int]:
        return (key >> 4) - 1, (key & 0xF) - 1

    def _dump_buttons(self, proj: Project, page: int) -> bytes:
        buff: list[bytes] = []

        ts = [t for t in proj.timestamps.v if t.page == page]

        for t in ts:
            buff.append(struct.pack("fB", t.time, self._pack_key(*t.pos)))

        return b"".join(buff)

    def _dump_lights(self, proj: Project) -> bytes:
        buff: list[bytes] = []

        for l in proj.lighting.v:
            buff.append(
                struct.pack("ffbbI", l.time, l.duration, *(l.offset), len(l.light))
            )

            buff.append(l.light.encode())

        return b"".join(buff)

    def _load_buttons(self, data: bytes, page: int) -> list[ProjButton]:
        btns: list[ProjButton] = []

        for i in range(0, len(data), 5):
            time, pos = struct.unpack("fB", data[i : i + 5])

            pos = self._unpack_key(pos)

            btns.append(ProjButton(round(time, 2), pos, page))

        return btns

    def _load_lights(self, data: bytes) -> list[ProjLight]:
        lights: list[ProjLight] = []

        idx: int = 0
        while idx < len(data) - 1:
            time, duration, offx, offy, slen = struct.unpack(
                "ffbbI", data[idx : idx + 16]
            )
            idx += 16

            name = data[idx : idx + slen].decode()
            idx += slen

            lights.append(ProjLight(name, round(time, 2), duration, (offx, offy)))

        return lights
