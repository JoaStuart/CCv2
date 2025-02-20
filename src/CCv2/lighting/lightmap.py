import abc
import os
from typing import ItemsView

import constants
import logger
from utils.color import col


class Lightmap:
    MAPS: "dict[str, Lightmap]" = {}

    @staticmethod
    def versions() -> "list[LightmapLoader]":
        return [LightmapV1()]

    @staticmethod
    def load_all() -> None:
        for m in os.listdir(constants.LIGHTMAPS):
            map_path = os.path.join(constants.LIGHTMAPS, m)
            logger.debug("Attempting to load Lightmap `%s`...", m)

            with open(map_path, "rb") as rf:
                data = rf.read()

            lightmap = Lightmap(m)

            for v in Lightmap.versions():
                if v.check(data):
                    v.load(lightmap, data)
                    logger.debug("Loaded %s as %s", m, v.__class__.__name__)
                    break
            else:
                logger.warning("Could not load %s as a Lightmap!", m)
                continue

            Lightmap.MAPS[lightmap.name] = lightmap

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

    def __len__(self) -> int:
        return len(self._mappings)

    def items(self) -> ItemsView[int, col]:
        return self._mappings.items()

    def __str__(self) -> str:
        return str(self._mappings)


class LightmapLoader(abc.ABC):
    @abc.abstractmethod
    def check(self, data: bytes) -> bool:
        pass

    @abc.abstractmethod
    def load(self, lightmap: Lightmap, data: bytes) -> None:
        pass

    @abc.abstractmethod
    def dump(self, lightmap: Lightmap) -> bytes:
        pass


class LightmapV1(LightmapLoader):
    def check(self, data: bytes) -> bool:
        return data[0] == 0x55 and data[1] == 0x1

    def load(self, lightmap: Lightmap, data: bytes) -> None:
        for i in range(2, len(data), 4):
            lightmap[data[i]] = col(
                data[i + 1],
                data[i + 2],
                data[i + 3],
            )

    def dump(self, lightmap: Lightmap) -> bytes:
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
