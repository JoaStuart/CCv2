import math
from re import L
from typing import Any, Optional
import dearpygui.dearpygui as dpg
import numpy as np
import pygame

from audio.audio_route import audio_router
import constants
from launchpad.route import LaunchpadReceiver
import logger
from project.project import ProjButton, Project
from audio.track import AudioTrack
from ptypes import int3
from singleton import singleton
from ui.main_ui import Window
from ui.props_ui import PropsWindow
from utils.color import col
from utils.runtime import RuntimeVars
from utils.ui_property import UiProperty


@singleton
class TrackWindow(Window, LaunchpadReceiver):
    DRAWLIST = "track_drawlist"
    DYNAMIC = "dynamic_layer"
    WAVEFORM = "waveform_layer"
    SCROLL = "scroll_drawlist"

    SECONDS_PER_SCREEN = 2
    TRACK_COLORS: list[col] = [
        col.hex(0x750000),
        col.hex(0x756400),
        col.hex(0x217500),
        col.hex(0x007543),
        col.hex(0x004375),
        col.hex(0x210075),
        col.hex(0x750064),
    ]

    def __init__(self) -> None:
        super().__init__("Track", "track")

        self._pos_cur: UiProperty[float] = UiProperty(0.0)
        self._pos_cur.add_listener(self._pos_change)
        self._waveform_redraw: bool = True

        self._pps = self._px_per_sample(700)
        self._spp = 1 / self._pps
        self._active_channel: Optional[pygame.mixer.Channel] = None

        RuntimeVars().page.add_listener(lambda _: self.redraw())

        proj = self._project()
        proj.tracks.add_listener(self._track_change)
        proj.timestamps.add_listener(lambda _: self.redraw())

    def _track_change(self, _tracks: list[AudioTrack]) -> None:
        self._waveform_redraw = True
        self.redraw()

    def _project(self) -> Project:
        return RuntimeVars().project

    def _px_per_sample(self, width: int) -> float:
        samples_in_view = self.SECONDS_PER_SCREEN * constants.SAMPLE_RATE
        return width / samples_in_view

    def _pos_change(self, new_pos: float) -> None:
        for t in self._project().timestamps.v:
            if t == new_pos * self._spp / constants.SAMPLE_RATE:
                PropsWindow().focus_button(t.time, t.pos)
                break
        else:
            PropsWindow().unfocus_button()

    def _on_click(self) -> None:
        if self._playing():
            return

        self._pos_cur.v = dpg.get_drawing_mouse_pos()[0]
        self.redraw()

    def _on_right(self) -> None:
        self._pos_cur.v = min(self._project().max_length(), self._pos_cur.v + 1)
        self.redraw()

    def _on_left(self) -> None:
        self._pos_cur.v = max(0, self._pos_cur.v - 1)
        self.redraw()

    def _on_next(self) -> None:
        ts = [t.time * constants.SAMPLE_RATE for t in self._project().timestamps.v]
        possible = [t for t in ts if t > self._pos_cur.v * self._spp]

        if len(possible) == 0:
            self._pos_cur.v = self._project().max_length() * self._pps
        else:
            self._pos_cur.v = possible[0] * self._pps

        self.redraw()

    def _on_prev(self) -> None:
        ts = [t.time * constants.SAMPLE_RATE for t in self._project().timestamps.v]
        possible = [t for t in ts if t < self._pos_cur.v * self._spp]

        if len(possible) == 0:
            self._pos_cur.v = 0
        else:
            self._pos_cur.v = possible[-1] * self._pps

        self.redraw()

    def _playing(self) -> bool:
        return self._active_channel is not None and self._active_channel.get_busy()

    def _play_pause(self) -> None:
        if self._playing():
            audio_router.stop(self._active_channel)  # type: ignore
            self._active_channel = None
        else:
            project = self._project()

            self._active_channel = audio_router.play(
                project.get_segment(
                    math.floor(self._pos_cur.v * self._spp),
                    project.max_length(),
                ),
                self._update_cur,
            )

    def _update_cur(self, elapsed: float) -> None:
        self._pos_cur.v += constants.SAMPLE_RATE * elapsed * self._pps

        dpg.set_x_scroll(self.SCROLL, self._pos_cur.v - 50)

        self.redraw()

    def setup(self) -> None:
        with dpg.child_window(
            width=700, height=300, horizontal_scrollbar=True, tag=self.SCROLL
        ):
            with dpg.drawlist(
                width=math.ceil(self._project().max_length() * self._pps),
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
            dpg.add_key_press_handler(key=dpg.mvKey_Left, callback=self._on_left)
            dpg.add_key_press_handler(key=dpg.mvKey_Period, callback=self._on_next)
            dpg.add_key_press_handler(key=dpg.mvKey_Comma, callback=self._on_prev)
            dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=self._play_pause)

        self.redraw()

    def _focus(self) -> None:
        LaunchpadReceiver.request_input(self)

    def redraw(self) -> None:
        dpg.delete_item(self.DYNAMIC, children_only=True)

        if self._waveform_redraw:
            dpg.delete_item(self.WAVEFORM, children_only=True)

        top = 270 / 2 - len(self._project().tracks.v) / 2 * 25

        for i, track in enumerate(self._project().tracks.v):
            pps = self._px_per_sample(700)

            dpg.draw_rectangle(
                (0, i * 25 + top),
                (track.track.shape[0] * pps, i * 25 + top + 20),
                color=(200, 200, 200),
                fill=self.TRACK_COLORS[i % len(self.TRACK_COLORS)].rgb,
                parent=self.DYNAMIC,
            )

            if self._waveform_redraw:
                center = (i * 25 + top) + 10

                spp = int(1 // pps)
                t = track.track
                logger.debug("Rendering WaveForm for track %d...", i)
                for j in range(0, t.shape[0], spp):
                    mx = (
                        (np.max(t[j : j + spp, 0]).item())
                        / np.iinfo(constants.SAMPLE_DEPTH).max
                        * 10
                    )

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

        max_height_tracks = len(self._project().tracks.v) * 25

        for t in self._project().timestamps.v:
            color = (255, 0, 0) if t.page == RuntimeVars().page.v else (50, 10, 0)

            dpg.draw_line(
                (t.time * constants.SAMPLE_RATE * self._px_per_sample(700), top),
                (
                    t.time * constants.SAMPLE_RATE * self._px_per_sample(700),
                    max_height_tracks + top - 5,
                ),
                color=color,
                thickness=2,
                parent=self.DYNAMIC,
            )

        if self._pos_cur.v >= 0:
            dpg.draw_line(
                (self._pos_cur.v, top),
                (self._pos_cur.v, max_height_tracks + top - 5),
                color=(200, 200, 200),
                thickness=2,
                parent=self.DYNAMIC,
            )

    def note_on(self, x: int, y: int) -> None:
        print(x, y)

        cur_sample = self._pos_cur.v * self._spp
        cur_time = cur_sample / constants.SAMPLE_RATE

        t = self._project().timestamps
        t.v.append(ProjButton(cur_time, (x, y), RuntimeVars().page.v))

        t.change()
        self._pos_cur.change()

    def note_off(self, x: int, y: int) -> None:
        return
