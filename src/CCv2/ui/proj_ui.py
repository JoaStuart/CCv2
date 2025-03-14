import os
from typing import Callable
import dearpygui.dearpygui as dpg

from audio.audio_route import AudioRouter
from audio.track import AudioTrack
import constants
from launchpad.route import LaunchpadReceiver
from lighting.generator import Generator
from project.project import Project
from ui.main_ui import Window
from ui.track_ui import TrackWindow
from utils.runtime import RuntimeVars


class ProjectWindow(Window, LaunchpadReceiver):
    SAVE_DIALOG = "proj_save"
    SAVED_DIALOG = "saved_dialog"

    def __init__(self) -> None:
        super().__init__("Project", "project")

    def setup(self) -> None:
        proj = self._project()

        self._draw_save_dialog()
        self._draw_menu()
        dpg.add_separator()
        self._draw_router()

        dpg.add_separator()
        self._draw_info(proj)

        dpg.add_separator()
        self._draw_track_volumes()

    def _draw_track_volumes(self) -> None:
        proj = RuntimeVars().project

        for t in proj.tracks.v:
            with dpg.group(horizontal=True):
                dpg.add_text(t.name)

                tag = hex(hash(t))
                dpg.add_slider_int(
                    tag=tag,
                    tracked=True,
                    callback=self._make_vol_callback(tag, t),
                    default_value=round(t.volume * 100),
                    clamped=True,
                    min_value=0,
                    max_value=100,
                )

    def _make_vol_callback(self, tag: str, track: AudioTrack) -> Callable[[], None]:
        def call() -> None:
            vol = dpg.get_value(tag)
            track.volume = vol / 100

        return call

    def _draw_router(self) -> None:
        self.main.selected_theme()

        dpg.add_text("Launchpad controls...")

        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Generator",
                tag="route_generator",
                callback=self._make_router_callback("route_generator"),
            )
            dpg.add_button(
                label="Creator",
                tag="route_creator",
                callback=self._make_router_callback("route_creator"),
            )
            dpg.add_button(
                label="Player",
                tag="route_player",
                callback=self._make_router_callback("route_player"),
            )

    def _make_router_callback(self, target: str) -> Callable[[], None]:
        cls_map: dict[str, LaunchpadReceiver] = {
            "route_generator": Generator(),
            "route_creator": TrackWindow(),
            "route_player": self,
        }

        win_map: dict[str, str] = {
            "route_generator": "generator",
            "route_creator": "track",
            "route_player": "launchpad",
        }

        def call() -> None:
            if target not in cls_map:
                return

            for t in cls_map.keys():
                dpg.enable_item(t)

            dpg.disable_item(target)
            LaunchpadReceiver.request_input(cls_map[target])

            dpg.focus_item(win_map[target])

        return call

    def _draw_save_dialog(self) -> None:
        lpath = self._project().load_path
        if lpath:
            name = os.path.splitext(os.path.split(lpath)[1])[0]
        else:
            name = "project"

        dpg.add_file_dialog(
            label="Save project as",
            show=False,
            tag=self.SAVE_DIALOG,
            modal=True,
            directory_selector=False,
            height=500,
            file_count=5000,
            default_filename=name,
            callback=self._save,
            cancel_callback=self._cancel,
        )

        with dpg.window(label="Saved!", modal=True, tag=self.SAVED_DIALOG, show=False):
            dpg.add_text("The project was saved!")
            dpg.add_button(
                label="Ok", callback=lambda: dpg.hide_item(self.SAVED_DIALOG)
            )

    def _save(self) -> None:
        data = dpg.get_file_dialog_info(self.SAVE_DIALOG)

        path: str = data["current_path"]
        name: str = data["file_name"]

        if not name.endswith(constants.PROJ_EXT):
            name += constants.PROJ_EXT

        full_path = os.path.join(path, name)
        self._project().save(full_path)

        dpg.show_item(self.SAVED_DIALOG)

    def _cancel(self) -> None:
        dpg.hide_item(self.SAVE_DIALOG)

    def _draw_menu(self) -> None:
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Save", callback=lambda: dpg.show_item(self.SAVE_DIALOG)
            )

    def _draw_info(self, proj: Project) -> None:
        with dpg.group(horizontal=True):
            dpg.add_text("Title:")
            dpg.add_text(proj.title)

        with dpg.group(horizontal=True):
            dpg.add_text("Length:")
            dpg.add_text(
                f"{round(proj.max_length() / constants.SAMPLE_RATE, ndigits=1)}s"
            )

        with dpg.item_handler_registry(tag="focus_proj"):
            dpg.add_item_focus_handler(callback=self._focus)
        dpg.bind_item_handler_registry("track", "focus_proj")

    def _focus(self) -> None:
        LaunchpadReceiver.request_input(self)

    def _project(self) -> Project:
        return RuntimeVars().project

    def note_on(self, x: int, y: int) -> None:
        proj = self._project().baked
        if not proj:
            return

        aud = proj.get(RuntimeVars().page.v, (x, y))

        if not aud:
            return

        AudioRouter().play(aud)

    def note_off(self, x: int, y: int) -> None:
        return
