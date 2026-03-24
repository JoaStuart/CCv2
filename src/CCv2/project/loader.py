import abc
import io
import json
import math
import os
import struct
from typing import Any

from ..utils.versioning import VersionLoader
from ..lighting.keyframes import Keyframes
from .. import constants
from .. import logger
from ..project.project import ProjButton, ProjDescription, ProjLight, Project


class ProjectV1(VersionLoader[Project]):
    def result(self) -> type[Project]:
        return Project

    def version(self) -> float:
        return 1.0

    def load(self, data: bytes, *args: Any) -> Project:
        tracks = Project.load_audio(constants.CACHE_AUDIO)
        proj_descr = self._load_project_descr()

        btns = self._read_buttons(proj_descr.get("pages").get_item("buttons", list))
        with open(os.path.join(constants.CACHE_PAGES, "lights.lpl"), "rb") as file:
            lights = VersionLoader.load_best(list[ProjLight], file.read())

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

                btns.extend(VersionLoader.load_best(list[ProjButton], data, p))

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

    def check(self, data: bytes) -> bool:
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

    def dump(self, proj: Project) -> bytes:
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

        return b""

    def _dump_page_btn(self, proj: Project, proj_data: dict[str, Any], p: int) -> None:
        buttons = [t for t in proj.timestamps.v if t.page == p]
        if len(buttons) == 0:
            return

        data = VersionLoader.dump_best(list[ProjButton], buttons)

        proj_data["pages"]["buttons"].append(p)

        with open(os.path.join(constants.CACHE_PAGES, f"{p}.lpb"), "wb") as file:
            file.write(data)

    def _dump_full_light(self, proj: Project) -> None:
        data = VersionLoader.dump_best(list[ProjLight], proj.lighting.v)

        with open(os.path.join(constants.CACHE_PAGES, "lights.lpl"), "wb") as file:
            file.write(data)


class LaunchpadButtonsV1(VersionLoader[list[ProjButton]]):
    def result(self):
        return list[ProjButton]

    def version(self) -> float:
        return math.nan

    def check(self, data: bytes) -> bool:
        return True  # V1 does not have a magic header, just check last

    def _pack_key(self, x: int, y: int) -> int:
        return ((x + 1) << 4) | (y + 1)

    def _unpack_key(self, key: int) -> tuple[int, int]:
        return (key >> 4) - 1, (key & 0xF) - 1

    def load(self, data: bytes, page: int, *args: Any) -> list[ProjButton]:
        btns: list[ProjButton] = []

        for i in range(0, len(data), 5):
            time, pos = struct.unpack("fB", data[i : i + 5])

            pos = self._unpack_key(pos)

            btns.append(ProjButton(round(time, 2), pos, page))

        return btns

    def dump(self, buttons: list[ProjButton], *args: Any) -> bytes:
        buff: list[bytes] = []

        for t in buttons:
            buff.append(struct.pack("fB", t.time, self._pack_key(*t.pos)))

        return b"".join(buff)


class LaunchpadButtonsV1_1(VersionLoader[list[ProjButton]]):
    def result(self):
        return list[ProjButton]

    def version(self) -> float:
        return 1.1

    def check(self, data: bytes) -> bool:
        return data[0] == 0x12 and data[1] == 0x11

    def load(self, data: bytes, page: int, *args: Any) -> list[ProjButton]:
        btns: list[ProjButton] = []
        reader = io.BytesIO(data)
        reader.read(2)

        while True:
            d = reader.read(6)
            if len(d) == 0:
                break

            time, posx, posy = struct.unpack("fbb", d)

            btns.append(ProjButton(round(time, 2), (posx, posy), page))

        return btns

    def dump(self, buttons: list[ProjButton], *args: Any) -> bytes:
        buff: list[bytes] = [b"\x12\x11"]

        for t in buttons:
            buff.append(struct.pack("fbb", t.time, *t.pos))

        return b"".join(buff)


class LaunchpadLightsV1(VersionLoader[list[ProjLight]]):
    def result(self):
        return list[ProjLight]

    def version(self) -> float:
        return math.nan

    def check(self, data: bytes) -> bool:
        return True  # V1 does not have a magic header, just check last

    def load(self, data: bytes, *args: Any) -> list[ProjLight]:
        lights: list[ProjLight] = []
        reader = io.BytesIO(data)

        while True:
            d = reader.read(16)
            if len(d) == 0:
                break

            time, duration, offx, offy, slen = struct.unpack("ffbbI", d)
            name = reader.read(slen).decode()

            lights.append(ProjLight(name, round(time, 2), duration, (offx, offy)))

        return lights

    def dump(self, obj: list[ProjLight], *args: Any) -> bytes:
        buff: list[bytes] = []

        for l in obj:
            buff.append(
                struct.pack("ffbbI", l.time, l.duration, *(l.offset), len(l.light))
            )

            buff.append(l.light.encode())

        return b"".join(buff)
