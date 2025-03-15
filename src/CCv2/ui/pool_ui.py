import os
import dearpygui.dearpygui as dpg

import constants
from ptypes import int2
from singleton import singleton
from ui.main_ui import Window


@singleton
class PoolWindow(Window):
    def __init__(self) -> None:
        super().__init__("Keyframe pool", "keyframes")

    def position(
        self, full_size: tuple[int, int], size: tuple[int, int]
    ) -> tuple[int, int]:
        return 0, full_size[1] // 2 - size[1] // 2

    def setup(self) -> None:
        self._menu_bar()
        dpg.add_spacer(height=5)

        self._pool()

    def _menu_bar(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(label="Reload", callback=self.reload)

    def _pool(self) -> None:
        dpg.add_child_window(tag="pool", width=200, height=200)
        self.reload()

    def reload(self) -> None:
        os.makedirs(constants.CACHE_KEYFRAMES, exist_ok=True)
        dpg.delete_item("pool", children_only=True)

        row = dpg.add_group(horizontal=True, parent="pool")
        items = 0

        for i in os.listdir(constants.CACHE_KEYFRAMES):
            if not i.endswith(constants.KEYFRAME_EXT):
                continue

            name, _ = os.path.splitext(i)

            dpg.add_button(label=name, parent=row)

            items += 1
            if items >= 3:
                row = dpg.add_group(horizontal=True, parent="pool")
