import os
from typing import Callable, Optional
import dearpygui.dearpygui as dpg

from .. import constants
from ..ptypes import int2
from ..singleton import singleton
from ..ui.main_ui import Window
from ..lighting.keyframes import Keyframes, Kf
from .. import logger
from ..utils.color import col

type tag = int | str


@singleton
class PoolWindow(Window):
    def __init__(self) -> None:
        self._pool_entries: dict[str, tuple[tag, tag]] = {}
        self._rendered_keyframes: dict[str, list[int | str]] = {}
        self._current_keyframes: dict[str, int] = {}

        super().__init__("Keyframe pool", "keyframes")

    def position(
        self, full_size: tuple[int, int], size: tuple[int, int]
    ) -> tuple[int, int]:
        """Calculate the position this window should sit at.
        See super class `Window`
        """

        return 0, full_size[1] // 2 - size[1] // 2

    def setup(self) -> None:
        """Setup the window"""

        self._menu_bar()
        dpg.add_spacer(height=5)

        self._pool()

    def _menu_bar(self) -> None:
        """Draws the menu bar"""

        with dpg.group(horizontal=True):
            dpg.add_button(label="Reload", callback=self.reload)

    def _pool(self) -> None:
        """Draws the pool window"""

        dpg.add_child_window(tag="pool", width=200, height=200)
        self.reload()

    def reload(self) -> None:
        """Reloads the contents of the pool window"""

        self._pool_entries = {}
        os.makedirs(constants.CACHE_KEYFRAMES, exist_ok=True)
        dpg.delete_item("pool", children_only=True)
        Keyframes.load()

        self.draw()

    def _make_preview(
        self, name: str, width: int = 10, height: int = 10, size: int = 4
    ) -> Optional[int | str]:
        kf = Keyframes.FRAME_CACHE.get(name, None)
        if kf is None:
            logger.info("Keyframe %s not found in cache", name)
            return None

        frames = kf.frame_buffer
        if len(frames) == 0:
            logger.info("No frames found for keyframe %s", name)
            return None

        textures: list[str | int] = []

        with dpg.texture_registry():
            for f in frames:
                data = self._render_frame(f, width, height, size)
                t = dpg.add_static_texture(width * size, height * size, data)
                textures.append(t)

        self._current_keyframes[name] = 0
        self._rendered_keyframes[name] = textures
        return textures[0]

    def _render_frame(
        self, frame: Kf, width: int, height: int, size: int
    ) -> list[float]:
        prev: list[float] = []

        for y in range(height):
            line: list[float] = []

            for x in range(width):
                pos = frame.get((x - 1, y - 1), None)

                if pos is None:
                    line.extend(self._mult([0, 0, 0, 0], size))
                else:
                    pos *= 4
                    line.extend(
                        self._mult([pos.r / 255, pos.g / 255, pos.b / 255, 1], size)
                    )

            for _ in range(size):
                prev.extend(line)

        return prev

    def _mult(self, extend: list[float], amount: int) -> list[float]:
        l = []
        for _ in range(amount):
            l.extend(extend)

        return l

    def draw(self) -> None:
        row = dpg.add_group(horizontal=True, parent="pool")
        items = 0

        for i in os.listdir(constants.CACHE_KEYFRAMES):
            if not i.endswith(constants.KEYFRAME_EXT):
                continue

            name, _ = os.path.splitext(i)

            with dpg.child_window(parent=row, width=80, height=90) as t:
                tex = self._make_preview(name)
                if tex is None:
                    logger.warning("No texture for keyframe pool entry `%s`", name)
                    continue

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=3)
                    im = dpg.add_image(tex)

                dpg.add_spacer(height=7)
                dpg.add_text(name)

                self._pool_entries[name] = (t, 0)

                with dpg.item_handler_registry() as i:
                    dpg.add_item_hover_handler(callback=self._make_hover(name, im))

                dpg.bind_item_handler_registry(t, i)

            items += 1
            if items >= 2:
                items = 0
                row = dpg.add_group(horizontal=True, parent="pool")

    def _make_hover(self, name: str, im: str | int) -> Callable[[], None]:
        def call() -> None:
            frames = self._rendered_keyframes[name]
            num = (self._current_keyframes[name] + 1) % len(frames)
            self._current_keyframes[name] = num

            dpg.configure_item(im, texture_tag=frames[num])

        return call
