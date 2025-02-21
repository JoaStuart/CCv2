import abc
import threading
import dearpygui.dearpygui as dpg

from launchpad.base import Launchpad
from launchpad.route import LaunchpadReceiver
from lighting.keyframes import Keyframes, PersistentKeyframes
from lighting.lightmanager import LightManager
from ptypes import int2
from singleton import singleton
from utils.color import col


@singleton
class Generator(LaunchpadReceiver):
    MAX_GRADIENT: int = 15

    def __init__(self) -> None:
        self._active_keys: dict[tuple[int, int], Light] = {}
        self._current_color: col = col.hex(0)
        self._current_gradient: list[col] = []
        self._light_type: type[Light] = StaticLight
        self._light_mapping: dict[str, type[Light]] = {
            "static": StaticLight,
            "gradient": GradientLight,
        }

        self._keyframe: Keyframes = Keyframes()
        self._color_receiver: str = "current"

    def next(self) -> None:
        store_map: dict[int2, col] = {}

        for k, v in self._active_keys.items():
            v.off_evt.set()
            v.off_evt = threading.Event()

            store_map[k] = v.peek()

            next_col = v.next()
            self._display(k, next_col, v.off_evt)

            if v.final():
                del self._active_keys[k]

        self._keyframe.append(store_map)

    @property
    def length(self) -> float:
        return self._keyframe.anim_time

    @length.setter
    def length(self, target: float) -> None:
        self._keyframe.anim_time = target

    @property
    def light_type(self) -> "type[Light]":
        return self._light_type

    @light_type.setter
    def light_type(self, target: str) -> None:
        self._light_type = self._light_mapping[target]

    @property
    def color(self) -> col:
        return self._current_color

    @color.setter
    def color(self, target: col) -> None:
        self._current_color = target

    @property
    def gradient(self) -> list[col]:
        g = self._current_gradient.copy()
        g.extend([col.rep(0) for _ in range(self.MAX_GRADIENT - len(g))])

        return g

    def add_gradient(self, target: col) -> None:
        if len(self._current_gradient) >= self.MAX_GRADIENT:
            return

        self._current_gradient.append(target)

    def remove_gradient(self, idx: int) -> None:
        if len(self._current_gradient) <= idx:
            return

        self._current_gradient.pop(idx)

    def new_color(self, color: col) -> None:
        if self._color_receiver == "current":
            self.color = color
        else:
            self.add_gradient(color)

    def color_receiver(self, receiver: str) -> None:
        self._color_receiver = receiver

    def note_on(self, x: int, y: int) -> None:
        if (x, y) in self._active_keys:
            k = self._active_keys[(x, y)]
            k.off_evt.set()

            del self._active_keys[(x, y)]
            return

        light = self._light_type(
            self._current_color, self._current_gradient, threading.Event()
        )
        self._display((x, y), light.next(), light.off_evt)

        self._active_keys[(x, y)] = light

    def _display(self, pos: int2, color: col, off: threading.Event) -> None:
        kf = PersistentKeyframes(off)
        kf.append({pos: color})
        LightManager().play_raw(kf)

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)

    def save(self, path: str) -> None:
        self.next()

        Keyframes.versions()[-1].dump(self._keyframe)

        self.clear()

    def clear(self) -> None:
        self._keyframe = Keyframes()
        self._active_keys = {}

    def display_all(self) -> None:
        for k, v in self._active_keys.items():
            v.off_evt = threading.Event()

            self._display(k, v.peek(), v.off_evt)

    def preview(self) -> None:
        if len(self._keyframe) == 0:
            return

        def run() -> None:
            for k, v in self._active_keys.items():
                v.off_evt.set()

            end = LightManager().play_raw(self._keyframe)
            end.wait()

            self.display_all()

        threading.Thread(target=run, name="KeyFrame preview", daemon=True).start()


class Light(abc.ABC):
    def __init__(
        self, current: col, gradient: list[col], off_evt: threading.Event
    ) -> None:
        self._current = current
        self._gradient = gradient
        self.off_evt = off_evt

        self._idx = 0

    @abc.abstractmethod
    def next(self) -> col:
        pass

    @abc.abstractmethod
    def final(self) -> bool:
        pass

    @abc.abstractmethod
    def peek(self) -> col:
        pass


class StaticLight(Light):
    def next(self) -> col:
        self._idx += 1
        return self._current

    def final(self) -> bool:
        return self._idx > 0

    def peek(self) -> col:
        return self._current


class GradientLight(Light):
    def next(self) -> col:
        self._idx += 1
        return self._gradient[self._idx - 1]

    def final(self) -> bool:
        return self._idx >= len(self._gradient)

    def peek(self) -> col:
        return self._gradient[self._idx + 1]
