from functools import partial
from typing import Callable, Optional
import pygame
import dearpygui.dearpygui as dpg

from launchpad.base import Launchpad
from lighting.generator import Generator
from lighting.lightmap import Lightmap
from ptypes import int2, int3, int4
from ui.main_ui import Window
from utils.color import col


class GeneratorWindow(Window):
    WIDTH = 20
    SPACING = 3

    def __init__(self) -> None:
        super().__init__("Generator", "generator")

    def _get_primary_lightmap(self) -> Lightmap:
        if len(Launchpad.OUTPUTS) == 0:
            return Lightmap.MAPS["Mk2+Realism"]

        return Lightmap.MAPS[Launchpad.OUTPUTS[0].lightmap()]

    def setup(self) -> None:
        lm = self._get_primary_lightmap()

        self._draw_tiles(lm)

        with dpg.group(horizontal=True, horizontal_spacing=10):
            self._draw_current_color(lm)
            self._draw_current_gradient(lm)

    def _draw_tiles(self, lm: Lightmap) -> None:
        with dpg.group(horizontal=True, horizontal_spacing=20):
            for i in range(2):
                with dpg.group(horizontal_spacing=2):
                    for y in range(8):
                        with dpg.group(horizontal=True, horizontal_spacing=2):
                            for x in range(8):
                                v = i * 64 + y * 8 + x

                                dpg.add_color_button(
                                    lm[v].gamma(4).rgb,
                                    label=f"{v}",
                                    width=self.WIDTH,
                                    height=self.WIDTH,
                                    callback=self._tile_click(v),
                                )

    def _tile_click(self, v: int) -> Callable[[], None]:
        def call():
            Generator().color = self._get_primary_lightmap()[v]

        return call

    def _draw_current_color(self, lm: Lightmap) -> None:
        dpg.add_color_button(
            Generator().color.gamma(2).rgb,
            label="Current Color",
            tag="current",
            width=self.WIDTH,
            height=self.WIDTH,
        )

    def _draw_current_gradient(self, lm: Lightmap) -> None:
        grad = Generator().gradient

        with dpg.group(horizontal=True, horizontal_spacing=2):
            for i in range(len(grad)):
                dpg.add_color_button(
                    (grad[i] * 4).rgb,
                    label=f"Gradient [{i}]",
                    width=self.WIDTH,
                    height=self.WIDTH,
                )

    def _calculate_pos(self, vel: int) -> int3:
        i = vel // 64
        vel -= i * 64

        y = vel // 8
        vel -= y * 8

        return vel, y, i

    def _calculate_position(self, vel: int) -> int4:
        x, y, i = self._calculate_pos(vel)

        left = 8 * self.WIDTH + 7 * self.SPACING + self.WIDTH

        return (
            i * left + x * self.WIDTH + x * self.SPACING + self.SPACING,
            y * self.WIDTH + y * self.SPACING + self.SPACING,
            self.WIDTH,
            self.WIDTH,
        )
