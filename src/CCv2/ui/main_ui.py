import abc
import os
import threading
import pygame
import dearpygui.dearpygui as dpg

from .. import logger
from .. import constants
from ..lighting.lightmanager import LightManager, LightReceiver
from ..ptypes import int2, int4
from ..singleton import singleton
from ..utils.color import col


@singleton
class WindowManager:
    def __init__(self) -> None:
        dpg.create_context()
        self._windows: list[Window] = []

    def open(self, *windows: "Window") -> None:
        for w in windows:
            with dpg.window(
                label=w.label,
                tag=w.tag,
                no_resize=True,
                autosize=True,
                no_close=True,
            ):
                self._windows.append(w)
                w.setup()

    def close(self) -> None:
        pygame.mixer.stop()
        dpg.destroy_context()

    def start(self, ui_show: threading.Event) -> None:
        dpg.create_viewport(
            title="CC/v2",
            width=1920,
            height=1080,
            small_icon=os.path.join(constants.INTERNAL_ICONS, "icon.png"),
            large_icon=os.path.join(constants.INTERNAL_ICONS, "icon.png"),
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_viewport_resize_callback(self.position_windows)

        dpg.set_frame_callback(2, self.position_windows)
        ui_show.set()
        dpg.start_dearpygui()

        self.close()

    def position_windows(self) -> None:
        full_size = dpg.get_viewport_width(), dpg.get_viewport_height()

        for w in self._windows:
            size = dpg.get_item_width(w.tag), dpg.get_item_height(w.tag)

            if size[0] is None or size[1] is None:
                logger.warning("Could not determine size for window %s", w.tag)
                continue

            pos = w.position(full_size, size)  # type: ignore # We tested for None above
            dpg.set_item_pos(w.tag, list(pos))

    def selected_theme(self) -> None:
        with dpg.theme() as selected_theme:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                color = col.hex(0x225376).rgb

                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, color)

        dpg.bind_theme(selected_theme)

    def disabled_theme(self) -> None:
        with dpg.theme() as disabled_theme:
            for c in [
                dpg.mvInputFloat,
                dpg.mvInputIntMulti,
                dpg.mvInputText,
                dpg.mvCheckbox,
            ]:
                with dpg.theme_component(c, enabled_state=False):
                    bg = col.hex(0x2D2D30).rgb

                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, bg)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, col.hex(0xABABAC).rgb)
                    dpg.add_theme_color(dpg.mvThemeCol_Button, bg)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, bg)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, bg)

        dpg.bind_theme(disabled_theme)


class Window(abc.ABC):
    @staticmethod
    def background() -> col:
        return col.hex(0x1E1E1E)

    def __init__(self, label: str, tag: str) -> None:
        self.label = label
        self.tag = tag

    @property
    def main(self):
        return WindowManager()

    @abc.abstractmethod
    def setup(self) -> None:
        pass

    def position(self, full_size: int2, size: int2) -> int2:
        return 0, 0


class LaunchpadWindow(Window, LightReceiver):
    WIDTH = 25
    SPACE = 3
    PADD = 5

    CENTER_COL = col.hex(0xCCCCCC)
    CTRLLR_COL = col.hex(0x303030)
    WHITE = col.hex(0xFFFFFF)

    def __init__(self) -> None:
        super().__init__("Launchpad", "launchpad")

        LightManager().add_light_receiver(self)

    def _button_size(self, x: int, y: int) -> int2:
        if x == 0 and y == 0:
            return self.WIDTH // 2, self.WIDTH // 2

        if y >= 9:
            return self.WIDTH, self.WIDTH // 2

        if x == 9 and y == 0:
            return self.WIDTH - 2, self.WIDTH - 2

        return self.WIDTH, self.WIDTH

    def _has_button(self, x: int, y: int) -> bool:
        if (x == 0 or x == 9) and y >= 9:
            return False

        return True

    def _button_move(self, x: int, y: int) -> int2:
        if x == 0 and y == 0:
            return self.WIDTH // 4, self.WIDTH // 4

        if y == 10:
            return 0, -self.WIDTH // 2

        if x == 9 and y == 0:
            return 1, 1

        return 0, 0

    def _button_center(self, x: int, y: int) -> bool:
        if x == 0 or x == 9 or y == 0 or y >= 9:
            return False

        return True

    def setup(self) -> None:
        for x in range(10):
            for y in range(11):
                if not self._has_button(x, y):
                    continue

                self._draw_key(x, y)

    def _button_position(self, x: int, y: int) -> int4:
        mx, my = self._button_move(x, y)
        w, h = self._button_size(x, y)

        return (
            x * (self.WIDTH + self.SPACE) + self.PADD + mx,
            y * (self.WIDTH + self.SPACE) + self.PADD + my,
            w,
            h,
        )

    def _draw_key(self, x: int, y: int) -> None:
        cx, cy, cw, ch = self._button_position(x, y)
        center = self._button_center(x, y)

        c = self.CENTER_COL if center else self.CTRLLR_COL
        dpg.add_color_button(
            default_value=c.rgb,
            width=cw,
            height=ch,
            pos=(cx, cy + 17),
            label=f"{x - 1}:{y - 1}",
            tag=f"{x - 1}:{y - 1}",
        )

    def __setitem__(self, pos: int2, c: col) -> None:
        x, y = pos
        dpg.configure_item(f"{x}:{y}", default_value=c.rgb)


def open_and_run(splash_finish: threading.Event) -> None:
    from ui.generator_ui import GeneratorWindow
    from ui.track_ui import TrackWindow
    from ui.props_ui import PropsWindow
    from ui.proj_ui import ProjectWindow
    from ui.pool_ui import PoolWindow

    man = WindowManager()
    man.open(
        LaunchpadWindow(),
        GeneratorWindow(),
        TrackWindow(),
        PropsWindow(),
        ProjectWindow(),
        PoolWindow(),
    )

    man.start(splash_finish)
