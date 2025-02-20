import abc
import threading
import dearpygui.dearpygui as dpg

from launchpad.route import LaunchpadReceiver
from lighting.keyframes import Keyframes, PersistentKeyframes
from lighting.lightmanager import LightManager
from ptypes import int2
from singleton import singleton
from utils.color import col


@singleton
class Generator(LaunchpadReceiver):
    def __init__(self) -> None:
        self._active_keys: dict[tuple[int, int], Light] = {}
        self._current_color: col = col.hex(0)
        self._current_gradient: list[col] = []
        self._light_type: type[Light] = StaticLight

        self._keyframe: Keyframes = Keyframes()

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
    def light_type(self) -> "type[Light]":
        return self._light_type

    @light_type.setter
    def light_type(self, target: "type[Light]") -> None:
        self._light_type = target

    @property
    def color(self) -> col:
        return self._current_color

    @color.setter
    def color(self, target: col) -> None:
        dpg.configure_item("current", default_value=(target * 4).rgb)
        self._current_color = target

    @property
    def gradient(self) -> list[col]:
        return self._current_gradient.copy()

    def add_gradient(self, target: col) -> None:
        self._current_gradient.append(target)

    def remove_gradient(self, idx: int) -> None:
        self._current_gradient.pop(idx)

    def note_on(self, x: int, y: int) -> None:
        if (x, y) in self._active_keys:
            k = self._active_keys[(x, y)]
            k.off_evt.set()

            del self._active_keys[(x, y)]
            return

        light = self._light_type(
            self._current_color, self._current_gradient, threading.Event()
        )
        self._display((x, y), light.peek(), light.off_evt)

        self._active_keys[(x, y)] = light

    def _display(self, pos: int2, color: col, off: threading.Event) -> None:
        kf = PersistentKeyframes(off)
        kf.append({pos: color})
        LightManager().play_raw(kf)

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)


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
