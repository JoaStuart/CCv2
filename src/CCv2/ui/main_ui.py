import abc
import os
from threading import Timer
import pygame
import pygame._sdl2.video
import dearpygui.dearpygui as dpg

import constants
from lighting.lightmanager import LightManager, LightReceiver
from ptypes import int2, int4
from singleton import singleton
from utils.color import col

pygame.init()
pygame.font.init()


@singleton
class WindowManager:
    def __init__(self) -> None:
        dpg.create_context()
        self._window_ids: list[str | int] = []

    def open(self, *windows: "Window") -> None:
        for w in windows:
            with dpg.window(
                label=w.label,
                tag=w.tag,
                no_resize=True,
                autosize=True,
                no_close=True,
            ) as win:
                self._window_ids.append(win)
                w.setup()

    def close(self) -> None:
        dpg.destroy_context()

    def start(self) -> None:
        dpg.create_viewport(
            title="CC/v2",
            width=1920,
            height=1080,
            small_icon=os.path.join(constants.INTERNAL_ICONS, "icon.ico"),
            large_icon=os.path.join(constants.INTERNAL_ICONS, "icon.ico"),
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()

    def selected_theme(self) -> None:
        with dpg.theme() as disabled_theme:
            with dpg.theme_component(dpg.mvButton, enabled_state=False):
                color = col.hex(0x225376).rgb

                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, color)

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
        )

    def __setitem__(self, pos: int2, c: col) -> None:
        x, y = pos
        dpg.configure_item(f"{x}:{y}", default_value=c.rgb)


def open_and_run() -> int:
    from ui.generator_ui import GeneratorWindow
    from ui.track_ui import TrackWindow

    man = WindowManager()
    man.open(
        LaunchpadWindow(),
        GeneratorWindow(),
        TrackWindow(),
    )

    man.start()
    return 0
