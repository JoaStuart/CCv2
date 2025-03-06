import abc
from io import BytesIO
import os
import struct
import threading
import time
from typing import Optional

import constants
import logger
from ptypes import int2
from utils.color import col


type Kf = dict[int2, col]


class Keyframes:
    FRAME_CACHE: "dict[str, Keyframes]" = {}

    @staticmethod
    def versions() -> "list[KeyframesLoader]":
        return [KeyframesV1()]

    @staticmethod
    def load_internal() -> None:
        for k in os.listdir(constants.INTERNAL_KEYFRAMES):
            name, _ = os.path.splitext(k)
            if not k.endswith(constants.KEYFRAME_EXT):
                continue

            logger.debug("Loading internal keyframes %s...", k)

            with open(os.path.join(constants.INTERNAL_KEYFRAMES, k), "rb") as rf:
                data = rf.read()

            for v in Keyframes.versions():
                if v.check(data):
                    Keyframes.FRAME_CACHE[f"__{name}"] = v.load(data)
                    break
            else:
                logger.warning("Could not load %s as keyframes!", k)

    def __init__(self) -> None:
        self._keyframes: list[Kf] = []
        self._current_frame: int = 0
        self._last_frame_time: float = 0
        self._anim_time: float = 0.3

    def next_wait(self) -> float:
        if len(self._keyframes) == 0:
            return 0

        return (
            self._last_frame_time + self._anim_time / len(self._keyframes)
        ) - time.time()

    def next(self) -> Optional[Kf]:
        if len(self._keyframes) <= self._current_frame:
            return None

        self._last_frame_time = time.time()

        frames = self._keyframes[self._current_frame]
        self._current_frame += 1
        return frames

    def last(self) -> Optional[Kf]:
        if self._current_frame == 0:
            return None

        return self._keyframes[self._current_frame - 1]

    def copy(self) -> "Keyframes":
        new = Keyframes()
        new._keyframes = self._keyframes
        new._anim_time = self._anim_time

        return new

    @property
    def frame(self) -> int:
        return self._current_frame

    @frame.setter
    def frame(self, val: int) -> None:
        self._current_frame = val

    @property
    def anim_time(self) -> float:
        return self._anim_time

    @anim_time.setter
    def anim_time(self, time: float) -> None:
        self._anim_time = time

    def num_frames(self) -> int:
        return len(self._keyframes)

    def append(self, frame: Kf) -> None:
        self._keyframes.append(frame)

    def persistent(self, evt: threading.Event) -> "PersistentKeyframes":
        pk = PersistentKeyframes(evt)
        pk._keyframes = self._keyframes
        pk._anim_time = self._anim_time

        return pk

    def __len__(self) -> int:
        return len(self._keyframes)


class PersistentKeyframes(Keyframes):
    def __init__(self, finish_event: threading.Event) -> None:
        super().__init__()
        self._finish_event = finish_event
        self._anim_time = 0.1

    def next(self) -> dict[tuple[int, int], col] | None:
        if self._finish_event.is_set():
            return None

        if self._current_frame >= len(self._keyframes):
            self._current_frame %= len(self._keyframes)

        return super().next()

    def copy(self) -> Keyframes:
        new = PersistentKeyframes(self._finish_event)
        new._keyframes = self._keyframes
        new._anim_time = self._anim_time

        return new


class KeyframesLoader(abc.ABC):
    @abc.abstractmethod
    def check(self, data: bytes) -> bool:
        pass

    @abc.abstractmethod
    def load(self, data: bytes) -> Keyframes:
        pass

    @abc.abstractmethod
    def dump(self, keyframes: Keyframes) -> bytes:
        pass


class KeyframesV1(KeyframesLoader):
    def check(self, data: bytes) -> bool:
        return data[0] == 0xCC and data[1] == 0x01

    def _pack_key(self, x: int, y: int) -> int:
        return ((x + 1) << 4) | (y + 1)

    def _unpack_key(self, key: int) -> tuple[int, int]:
        return (key >> 4) - 1, (key & 0xF) - 1

    def load(self, data: bytes) -> Keyframes:
        f = BytesIO(data)
        f.read(2)  # Skip header because it was checked using `check`
        keyframes = Keyframes()

        keyframes.anim_time = struct.unpack("f", f.read(4))[0]
        num_frames = struct.unpack("I", f.read(4))[0]

        for _ in range(num_frames):
            num_pairs = struct.unpack("I", f.read(4))[0]
            d: dict[tuple[int, int], col] = {}
            for _ in range(num_pairs):
                packed_key = struct.unpack("B", f.read(1))[0]
                c = struct.unpack("BBB", f.read(3))
                d[self._unpack_key(packed_key)] = col(*c)
            keyframes.append(d)

        return keyframes

    def dump(self, keyframes: Keyframes) -> bytes:
        data: list[bytes] = [b"\xCC\x01"]

        data.append(struct.pack("f", keyframes.anim_time))
        data.append(struct.pack("I", keyframes.num_frames()))

        while (d := keyframes.next()) is not None:
            data.append(struct.pack("I", len(d)))
            for (x, y), value in d.items():
                data.append(struct.pack("B", self._pack_key(x, y)))
                data.append(struct.pack("BBB", *(value.rgb)))

        return b"".join(data)
