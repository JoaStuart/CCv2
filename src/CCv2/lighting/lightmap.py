import os
from typing import Any, ItemsView

from ..utils.versioning import VersionException, VersionLoader
from .. import constants
from .. import logger
from ..utils.color import col


class Lightmap:
    MAPS: "dict[str, Lightmap]" = {}

    @staticmethod
    def load_all() -> None:
        for m in os.listdir(constants.LIGHTMAPS):
            if not m.endswith(constants.LIGHTMAP_EXT):
                continue

            map_path = os.path.join(constants.LIGHTMAPS, m)
            logger.debug("Attempting to load Lightmap `%s`...", m)

            with open(map_path, "rb") as rf:
                data = rf.read()

            name = os.path.splitext(m)[0]

            try:
                lightmap = VersionLoader.load_best(Lightmap, data, name)
                logger.debug("Loaded lightmap %s", m)
                Lightmap.MAPS[lightmap.name] = lightmap

            except VersionException:
                logger.warning("Could not load %s as a Lightmap!", m)

    def __init__(self, name: str) -> None:
        self._mappings: dict[int, col] = {}
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    def __setitem__(self, key: int, val: col) -> None:
        self._mappings[key] = val

    def __getitem__(self, key: int) -> col:
        return self._mappings.get(key, col(255, 255, 255))

    def vel(self, c: col) -> int:
        for k, v in self._mappings.items():
            if v == c:
                return k

        return 0

    def closest(self, c: col) -> int:
        if sum(c.rgb) == 0:
            return 0

        if (v := self.vel(c)) != 0:
            return v

        best = 0
        dist = 0xFFFFFF
        for k, v in self._mappings.items():
            if k == 0:
                continue

            d = c.hsldist(v)

            if d < dist:
                best = k
                dist = d

        return best

    def __len__(self) -> int:
        return len(self._mappings)

    def items(self) -> ItemsView[int, col]:
        return self._mappings.items()

    def __str__(self) -> str:
        return str(self._mappings)


class LightmapV1(VersionLoader[Lightmap]):
    def result(self) -> type[Lightmap]:
        return Lightmap

    def version(self) -> float:
        return 1.0

    def check(self, data: bytes) -> bool:
        return data[0] == 0x55 and data[1] == 0x1

    def load(self, data: bytes, name: str, *args: Any) -> Lightmap:
        lm = Lightmap(name)

        for i in range(2, len(data), 4):
            lm[data[i]] = col(
                data[i + 1],
                data[i + 2],
                data[i + 3],
            )

        return lm

    def dump(self, lightmap: Lightmap, *args: Any) -> bytes:
        data = bytearray(len(lightmap) * 4 + 2)
        data[0] = 0x55
        data[1] = 0x01

        data_idx = 2
        for k, v in lightmap.items():
            data[data_idx] = k
            data[data_idx + 1] = v.r
            data[data_idx + 2] = v.g
            data[data_idx + 3] = v.b

            data_idx += 4

        return bytes(data)
