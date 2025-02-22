import math
from re import L
import dearpygui.dearpygui as dpg
import numpy as np

import constants
import logger
from project.project import Project
from ptypes import int3
from ui.main_ui import Window
from utils.color import col


class TrackWindow(Window):
    DRAWLIST = "track_drawlist"
    DYNAMIC = "dynamic_layer"
    WAVEFORM = "waveform_layer"

    SECONDS_PER_SCREEN = 2

    def __init__(self) -> None:
        super().__init__("Track", "track")

        self._pos_cur: int = -1
        self._waveform_redraw: bool = True
        self._focused: bool = False

        self._track_colors: list[col] = [
            col.hex(0x750000),
            col.hex(0x756400),
            col.hex(0x217500),
            col.hex(0x007543),
            col.hex(0x004375),
            col.hex(0x210075),
            col.hex(0x750064),
        ]

    def _project(self) -> Project:
        return constants.RUNTIME.project

    def _px_per_sample(self, width: int) -> float:
        samples_in_view = self.SECONDS_PER_SCREEN * constants.SAMPLE_RATE
        return width / samples_in_view

    def _on_focus(self, sender, parent) -> None:
        logger.info("%s, %s", str(sender), str(parent))
        self._focused = sender == dpg.get_alias_id("track")

    def _on_click(self) -> None:
        self._pos_cur = dpg.get_drawing_mouse_pos()[0]
        self.redraw()

    def _on_right(self) -> None:
        if not self._focused:
            return

        logger.info("RIGHT")
        self._pos_cur += 1
        self.redraw()

    def setup(self) -> None:
        with dpg.child_window(width=700, height=300, horizontal_scrollbar=True):
            with dpg.drawlist(
                width=math.ceil(
                    self._project().max_length() * self._px_per_sample(700)
                ),
                height=270,
                tag=self.DRAWLIST,
            ):
                dpg.add_draw_layer(tag=self.DYNAMIC)
                dpg.add_draw_layer(tag=self.WAVEFORM)

        with dpg.item_handler_registry(tag="drawlist_handlers"):
            dpg.add_item_clicked_handler(callback=self._on_click)

        dpg.bind_item_handler_registry(self.DRAWLIST, "drawlist_handlers")

        with dpg.handler_registry(tag="track_key_handler"):
            dpg.add_key_press_handler(key=dpg.mvKey_Right, callback=self._on_right)

        with dpg.item_handler_registry(tag="track_focus_handler"):
            dpg.add_item_focus_handler(callback=self._on_focus)

        dpg.bind_item_handler_registry("track", "track_focus_handler")

        self.redraw()

    def redraw(self) -> None:
        dpg.delete_item(self.DYNAMIC, children_only=True)

        if self._waveform_redraw:
            dpg.delete_item(self.WAVEFORM, children_only=True)

        top = 270 / 2 - len(self._project().tracks) / 2 * 25

        for i, track in enumerate(self._project().tracks):
            pps = self._px_per_sample(700)

            dpg.draw_rectangle(
                (0, i * 25 + top),
                (track.track.shape[1] * pps, i * 25 + top + 20),
                color=(200, 200, 200),
                fill=self._track_colors[i % len(self._track_colors)].rgb,
                parent=self.DYNAMIC,
            )

            if self._waveform_redraw:
                center = (i * 25 + top) + 10

                spp = int(1 // pps)
                t = track.track
                logger.debug("Rendering WaveForm for track %d...", i)
                for j in range(0, t.shape[1], spp):
                    mx = np.max(t[0, j : j + spp]) * 10

                    dpg.draw_line(
                        (j // spp, center - mx),
                        (j // spp, center + mx),
                        color=(0, 0, 0),
                        thickness=1,
                        parent=self.WAVEFORM,
                    )

        if self._waveform_redraw:
            logger.debug("Finished rendering WaveForms!")
            self._waveform_redraw = False

        max_height_tracks = len(self._project().tracks) * 25

        # for x, w in BLOCKS:
        #     dpg.draw_rectangle((x, 20), (x + w, 130), color=(0, 255, 0, 255),
        #                     fill=(0, 255, 0, 100), parent=self.DYNAMIC)

        for t, pos in self._project().buttons:
            dpg.draw_line(
                (t * constants.SAMPLE_RATE * self._px_per_sample(700), top),
                (
                    t * constants.SAMPLE_RATE * self._px_per_sample(700),
                    max_height_tracks + top,
                ),
                color=(255, 0, 0, 255),
                thickness=2,
                parent=self.DYNAMIC,
            )

        if self._pos_cur >= 0:
            dpg.draw_line(
                (self._pos_cur, top),
                (self._pos_cur, max_height_tracks + top),
                color=(200, 200, 200),
                thickness=2,
                parent=self.DYNAMIC,
            )
