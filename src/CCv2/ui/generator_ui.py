from functools import partial
import os
from typing import Callable, Optional
import pygame
import dearpygui.dearpygui as dpg

import constants
from launchpad.base import Launchpad
from launchpad.route import LaunchpadReceiver, LaunchpadRouter
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

        gen = Generator()
        gen.color_receiver.add_listener(lambda s: self._color_switch(s)(False))  # type: ignore

    def _get_primary_lightmap(self) -> Lightmap:
        if len(Launchpad.OUTPUTS) == 0:
            return Lightmap.MAPS["Mk2+Realism"]

        return Lightmap.MAPS[Launchpad.OUTPUTS[0].lightmap()]

    def setup(self) -> None:
        lm = self._get_primary_lightmap()

        self._draw_tiles(lm)

        with dpg.group(horizontal=True, horizontal_spacing=20):
            self._draw_current_color(lm)
            self._draw_current_gradient(lm)

        self._draw_color_switch()
        self._draw_light_switch()

        self._draw_length()
        dpg.add_spacer(height=20)
        self._draw_controls()

    def _focus(self) -> None:
        if LaunchpadReceiver.ACTIVE_RECEIVER == Generator():
            return

        LaunchpadReceiver.request_input(Generator())

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
            Generator().new_color(self._get_primary_lightmap()[v])

            self._redraw_current()

        return call

    def _redraw_current(self) -> None:
        grad = (gen := Generator()).gradient

        dpg.configure_item("current", default_value=(gen.color * 4).rgb)

        for i in range(gen.MAX_GRADIENT):
            dpg.configure_item(f"gradient_{i}", default_value=(grad[i] * 4).rgb)

    def _draw_current_color(self, lm: Lightmap) -> None:
        dpg.add_color_button(
            Generator().color.gamma(2).rgb,
            label="Current Color",
            tag="current",
            width=self.WIDTH,
            height=self.WIDTH,
        )

    def _draw_current_gradient(self, lm: Lightmap) -> None:
        grad = (gen := Generator()).gradient

        with dpg.group(horizontal=True, horizontal_spacing=2):
            for i in range(gen.MAX_GRADIENT):
                dpg.add_color_button(
                    (grad[i] * 4).rgb,
                    label=f"Gradient [{i}]",
                    tag=f"gradient_{i}",
                    callback=self._remove_gradient(i),
                    width=self.WIDTH,
                    height=self.WIDTH,
                )

    def _remove_gradient(self, i: int) -> Callable[[], None]:
        def call() -> None:
            Generator().remove_gradient(i)
            self._redraw_current()

        return call

    def _draw_color_switch(self) -> None:
        self.main.selected_theme()

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Current Color",
                tag="color_current",
                enabled=False,
                callback=self._color_switch("current"),
            )
            dpg.add_button(
                label="Gradient",
                tag="color_gradient",
                callback=self._color_switch("gradient"),
            )

    def _color_switch(self, target: str) -> Callable[[], None]:
        def call(change: bool = True):
            dpg.enable_item("color_current")
            dpg.enable_item("color_gradient")

            dpg.disable_item(f"color_{target}")

            if change:
                Generator().color_receiver.v = target

        return call

    def _draw_light_switch(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Static Light",
                tag="light_static",
                enabled=False,
                callback=self._light_switch("static"),
            )
            dpg.add_button(
                label="Gradient Light",
                tag="light_gradient",
                callback=self._light_switch("gradient"),
            )

    def _draw_controls(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=180)
            dpg.add_button(label="Preview", callback=Generator().preview)
            dpg.add_button(label="Next Frame", callback=Generator().next)
            dpg.add_button(
                label="Save", callback=lambda: dpg.show_item("generator_save")
            )

        with dpg.window(
            label="Save as...",
            modal=True,
            show=False,
            tag="generator_save",
            no_title_bar=True,
        ):
            dpg.add_text("What should the name of the KeyFrames be?")
            dpg.add_separator()
            dpg.add_spacer(height=10)
            dpg.add_input_text(
                hint="Name.kf",
                tag="generator_saveas",
                on_enter=True,
                callback=self._proceed_save,
            )
            dpg.add_spacer(height=20)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=150)
                dpg.add_button(label="Cancel", width=75, callback=self._cancel_save)
                dpg.add_button(label="Save", width=75, callback=self._proceed_save)

    def _cancel_save(self) -> None:
        dpg.hide_item("generator_save")
        dpg.set_value("generator_saveas", "")

    def _proceed_save(self) -> None:
        name = dpg.get_value("generator_saveas")
        self._cancel_save()

        Generator().save(os.path.join(constants.CACHE_KEYFRAMES, name))

        dpg.set_value("generator_length", Generator().length)

    def _light_switch(self, target: str) -> Callable[[], None]:
        def call() -> None:
            dpg.enable_item("light_static")
            dpg.enable_item("light_gradient")
            dpg.disable_item(f"light_{target}")

            Generator().light_type = target

        return call

    def _draw_length(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text("Default length:")
            dpg.add_spacer()
            dpg.add_input_float(
                tag="generator_length",
                step=0.01,
                format="%.2f",
                min_clamped=True,
                max_clamped=True,
                callback=self._set_length,
            )

    def _set_length(self) -> None:
        length = dpg.get_value("generator_length")
        Generator().length = length

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
