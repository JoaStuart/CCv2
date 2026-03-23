import os
from typing import Callable
import dearpygui.dearpygui as dpg

from ..audio.audio_route import AudioRouter
from ..audio.track import AudioTrack
from .. import constants
from ..launchpad.base import Launchpad
from ..launchpad.route import LaunchpadReceiver
from ..lighting.generator import Generator
from ..lighting.lightmanager import LightManager
from ..ui.main_ui import Window
from ..ui.notif_ui import Notification
from ..project.baking import BakedProject
from ..project.project import Project
from ..ui.track_ui import TrackWindow


class ProjectWindow(Window, LaunchpadReceiver):
    SAVE_DIALOG = "proj_save"

    VISUALIZE: bool = False

    def __init__(self) -> None:
        super().__init__("Project", "project")

    def position(
        self, full_size: tuple[int, int], size: tuple[int, int]
    ) -> tuple[int, int]:
        """Calculate the position this window should sit at.
        See super class `Window`
        """

        return full_size[0] - size[0], 0

    def _spacer(self) -> None:
        """Draw a spaced out separator"""

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=10)

    def setup(self) -> None:
        """Setup the window"""

        proj = self._project()

        self._draw_save_dialog()
        self._draw_menu_bar()
        self._draw_info(proj)

        self._spacer()
        self._draw_router()
        dpg.add_checkbox(
            label="Visualize Launchpad",
            tag="visualize",
            callback=self._vis_check,
            tracked=True,
        )

        self._spacer()
        self._draw_track_volumes()

        self._spacer()
        dpg.add_button(
            label="Bake project [DEBUG]",
            callback=lambda: Project.CURRENT_PROJECT.v.bake(),
        )

    def _vis_check(self) -> None:
        """Callback for visualization checkbox"""

        ProjectWindow.VISUALIZE = dpg.get_value("visualize")

    def _draw_track_volumes(self) -> None:
        """Draws the volume sliders for all tracks"""

        proj = Project.CURRENT_PROJECT.v

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
        """Makes the track volume change callback listener

        Args:
            tag (str): The tag of the slider
            track (AudioTrack): The track corresponding to the tag

        Returns:
            Callable[[], None]: The callback listener
        """

        def call() -> None:
            vol = dpg.get_value(tag)
            track.volume = vol / 100

        return call

    def _draw_router(self) -> None:
        """Draws the launchpad routing interface"""

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
        """Makes the router callback handler

        Args:
            target (str): The target to which to route input

        Returns:
            Callable[[], None]: The callback listener
        """

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
        """Draws the save dialog window"""

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

    def _save(self) -> None:
        """Saves the current project to a file"""

        data = dpg.get_file_dialog_info(self.SAVE_DIALOG)

        path: str = data["current_path"]
        name: str = data["file_name"]

        if not name.endswith(constants.PROJ_EXT):
            name += constants.PROJ_EXT

        full_path = os.path.join(path, name)
        self._project().save(full_path)

        Notification("Project", "The project was saved successfully!")

    def _cancel(self) -> None:
        """Cancels the save operation"""

        dpg.hide_item(self.SAVE_DIALOG)

    def _draw_menu_bar(self) -> None:
        """Draws the menu portion of the window"""

        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(
                    label="Save", callback=lambda: dpg.show_item(self.SAVE_DIALOG)
                )
                dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

    def _draw_info(self, proj: Project) -> None:
        """Draws the project info for the given project

        Args:
            proj (Project): The project to display information for
        """

        with dpg.group(horizontal=True):
            dpg.add_text("Title:")
            dpg.add_text(proj.title)

        with dpg.group(horizontal=True):
            dpg.add_text("Length:")
            dpg.add_text(
                f"{round(proj.max_length() / constants.SAMPLE_RATE, ndigits=1)}s"
            )

    def _project(self) -> Project:
        """
        Returns:
            Project: The currently loaded project
        """

        return Project.CURRENT_PROJECT.v

    def note_on(self, x: int, y: int) -> None:
        """Note on handler for launchpad routing

        Args:
            x (int): The X position
            y (int): The Y position
        """

        proj = self._project().baked
        if not proj:
            return

        self._play_note(proj, x, y)
        self._play_light(proj, x, y)

    def _play_note(self, proj: BakedProject, x: int, y: int) -> None:
        aud = proj.get_audio(Launchpad.PAGE.v, (x, y))

        if aud is None:
            return

        AudioRouter().play(aud)

    def _play_light(self, proj: BakedProject, x: int, y: int) -> None:
        light = proj.get_light(Launchpad.PAGE.v, (x, y))

        if light is None:
            return

        for l in light:
            LightManager().play_after(*l)

    def note_off(self, x: int, y: int) -> None:
        """Note off handler for launchpad routing

        Args:
            x (int): The X position
            y (int): The Y position
        """

        pass
