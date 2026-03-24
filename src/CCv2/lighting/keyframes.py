from io import BytesIO
import io
import os
import struct
import threading
import time
from typing import Any, Callable, Optional

import av
from av import VideoStream
import numpy as np

from ..utils.versioning import VersionException, VersionLoader
from ..utils.data_uri import make_data_uri
from ..utils.daemon_thread import DaemonThread
from .. import constants
from .. import logger
from ..ptypes import int2
from ..utils.color import col


type Kf = dict[int2, col]


class KeyframesPreview(DaemonThread):
    def __init__(self) -> None:
        self._requested: list[tuple[str, Keyframes]] = []
        self._requested_event = threading.Event()

        super().__init__("KeyframesPreview")

    def request(self, name: str, kf: "Keyframes") -> None:
        self._requested.append((name, kf))
        self._requested_event.set()

    def thread_loop(self) -> None:
        if len(self._requested) == 0:
            self._requested_event.wait()
            self._requested_event.clear()
        else:
            name, r = self._requested.pop(0)

            tbegin = time.time()
            r._preview = r.to_mp4_uri()
            tdiff = time.time() - tbegin
            if tdiff > 0.1:
                logger.info("Took long time for preview of %s in %.2fs", name, tdiff)

            if Keyframes.PREVIEW_COMPLETED is not None:
                Keyframes.PREVIEW_COMPLETED(name, r)

    def thread_cleanup(self) -> None:
        return self._requested_event.set()

    def __len__(self) -> int:
        return len(self._requested)


class Keyframes:
    FRAME_CACHE: "dict[str, Keyframes]" = {}
    PREVIEW_COMPLETED: Optional[Callable[[str, Keyframes], None]] = None
    LOAD_COMPLETED: Optional[Callable[[None], None]] = None

    PREVIEW_THREADS = [
        KeyframesPreview(),
        KeyframesPreview(),
    ]

    @staticmethod
    def preview_request(name: str, frame: "Keyframes") -> None:
        amnt, thread = len(Keyframes.PREVIEW_THREADS[0]), Keyframes.PREVIEW_THREADS[0]

        for t in Keyframes.PREVIEW_THREADS:
            if len(t) < amnt:
                amnt, thread = len(t), t

        thread.request(name, frame)

    @staticmethod
    def load_internal() -> None:
        for k in os.listdir(constants.INTERNAL_KEYFRAMES):
            name, _ = os.path.splitext(k)
            if not k.endswith(constants.KEYFRAME_EXT):
                continue

            logger.debug("Loading internal keyframes %s...", k)

            with open(os.path.join(constants.INTERNAL_KEYFRAMES, k), "rb") as rf:
                data = rf.read()

            try:
                Keyframes.FRAME_CACHE[f"__{name}"] = VersionLoader.load_best(
                    Keyframes, data
                )
            except VersionException:
                logger.warning("Could not load %s as keyframes!", k)

    @staticmethod
    def load() -> None:
        for k in os.listdir(constants.CACHE_KEYFRAMES):
            name, _ = os.path.splitext(k)
            if not k.endswith(constants.KEYFRAME_EXT):
                continue

            logger.debug("Loading project keyframes %s...", k)

            with open(os.path.join(constants.CACHE_KEYFRAMES, k), "rb") as rf:
                data = rf.read()

            try:
                Keyframes.FRAME_CACHE[name] = frame = VersionLoader.load_best(
                    Keyframes, data
                )
                Keyframes.preview_request(name, frame)
            except VersionException:
                logger.warning("Could not load %s as keyframes!", k)

        if Keyframes.LOAD_COMPLETED is not None:
            Keyframes.LOAD_COMPLETED(None)

    @staticmethod
    def dump() -> None:
        for name, kf in Keyframes.FRAME_CACHE.items():
            if name.startswith("__"):
                continue

            with open(
                os.path.join(constants.CACHE_KEYFRAMES, f"{name}.lpk"), "wb"
            ) as wf:
                wf.write(VersionLoader.dump_best(Keyframes, kf))

    def __init__(self) -> None:
        self._keyframes: list[Kf] = []
        self._current_frame: int = 0
        self._last_frame_time: float = 0
        self._anim_time: float = 0.3
        self._static_after: bool = False
        self._preview: Optional[str] = None

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
        new._static_after = self._static_after
        new._preview = self._preview

        return new

    def to_mp4_uri(self) -> str:
        fps = int(len(self) / self.anim_time)

        buffer = io.BytesIO()
        container = av.open(buffer, mode="w", format="mp4")
        stream: VideoStream = container.add_stream("libx264", rate=fps)
        stream.width = stream.height = 10
        stream.pix_fmt = "yuv420p"
        stream.codec_context.gop_size = 1
        stream.codec_context.options = {"preset": "ultrafast", "tune": "zerolatency"}

        for kf in self._keyframes:
            frame = np.zeros((stream.height, stream.width, 3), dtype=np.uint8)

            for (x, y), col in kf.items():
                if y > 8:
                    y = 8
                try:
                    frame[y + 1, x + 1, :] = (col * 4).rgb
                except IndexError:
                    pass

            vid_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
            vid_frame = vid_frame.reformat(
                stream.width, stream.height, format="yuv420p"
            )

            for p in stream.encode(vid_frame):
                container.mux(p)

        for p in stream.encode():
            container.mux(p)

        container.close()

        return make_data_uri(buffer.getvalue(), "video/mp4")

    @property
    def static_after(self) -> bool:
        return self._static_after

    @property
    def frame(self) -> int:
        return self._current_frame

    @frame.setter
    def frame(self, val: int) -> None:
        self._current_frame = val

    @property
    def frame_buffer(self) -> list[Kf]:
        return self._keyframes

    @property
    def anim_time(self) -> float:
        return self._anim_time

    @anim_time.setter
    def anim_time(self, time: float) -> None:
        self._static_after = time < 0
        self._anim_time = abs(time)

    @property
    def preview(self) -> Optional[str]:
        return self._preview

    @preview.setter
    def preview(self, data: str) -> None:
        self._preview = data

    def num_frames(self) -> int:
        return len(self._keyframes)

    def append(self, frame: Kf) -> None:
        self._keyframes.append(frame)

    def persistent(self, evt: threading.Event) -> "PersistentKeyframes":
        pk = PersistentKeyframes(evt)
        pk._keyframes = self._keyframes
        pk._anim_time = self._anim_time
        pk._static_after = self._static_after

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


class KeyframesV1(VersionLoader[Keyframes]):
    def result(self) -> type[Keyframes]:
        return Keyframes

    def version(self) -> float:
        return 1.0

    def check(self, data: bytes) -> bool:
        return data[0] == 0xCC and data[1] == 0x01

    def _pack_key(self, x: int, y: int) -> int:
        return ((x + 1) << 4) | (y + 1)

    def _unpack_key(self, key: int) -> tuple[int, int]:
        return (key >> 4) - 1, (key & 0xF) - 1

    def load(self, data: bytes, *args: Any) -> Keyframes:
        f = BytesIO(data)
        f.read(2)  # Skip header because it was checked using `check`
        keyframes = Keyframes()

        keyframes.anim_time = struct.unpack("f", f.read(4))[0]
        num_frames = struct.unpack("I", f.read(4))[0]

        try:
            for _ in range(num_frames):
                num_pairs = struct.unpack("I", f.read(4))[0]
                d: dict[tuple[int, int], col] = {}
                for _ in range(num_pairs):
                    packed_key = struct.unpack("B", f.read(1))[0]
                    c = struct.unpack("BBB", f.read(3))
                    d[self._unpack_key(packed_key)] = col(*c)
                keyframes.append(d)
        except Exception:
            pass

        return keyframes

    def dump(self, keyframes: Keyframes, *args: Any) -> bytes:
        data: list[bytes] = [b"\xcc\x01"]

        static = -1 if keyframes.static_after else 1
        data.append(struct.pack("f", keyframes.anim_time * static))
        data.append(struct.pack("I", keyframes.num_frames()))

        for d in keyframes.frame_buffer:
            data.append(struct.pack("I", len(d)))
            for (x, y), value in d.items():
                data.append(struct.pack("B", self._pack_key(x, y)))
                data.append(struct.pack("BBB", *(value.rgb)))

        return b"".join(data)


class KeyframesV1_1(VersionLoader[Keyframes]):
    def result(self) -> type[Keyframes]:
        return Keyframes

    def version(self) -> float:
        return 1.1

    def check(self, data: bytes) -> bool:
        return data[0] == 0xCC and data[1] == 0x11

    def load(self, data: bytes, *args: Any) -> Keyframes:
        f = BytesIO(data)
        f.read(2)  # Skip header because it was checked using `check`
        keyframes = Keyframes()

        keyframes.anim_time = struct.unpack("f", f.read(4))[0]
        num_frames = struct.unpack("I", f.read(4))[0]

        for _ in range(num_frames):
            num_pairs = struct.unpack("I", f.read(4))[0]
            d: dict[tuple[int, int], col] = {}
            for _ in range(num_pairs):
                x, y, _special = struct.unpack("bbB", f.read(3))
                c = struct.unpack("BBB", f.read(3))
                d[x, y] = col(*c)
            keyframes.append(d)

        return keyframes

    def dump(self, keyframes: Keyframes, *args: Any) -> bytes:
        data: list[bytes] = [b"\xcc\x11"]

        static = -1 if keyframes.static_after else 1
        data.append(struct.pack("f", keyframes.anim_time * static))
        data.append(struct.pack("I", keyframes.num_frames()))

        for d in keyframes.frame_buffer:
            data.append(struct.pack("I", len(d)))
            for (x, y), value in d.items():
                data.append(struct.pack("bbB", x, y, 0))
                data.append(struct.pack("BBB", *(value.rgb)))

        return b"".join(data)
