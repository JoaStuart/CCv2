import os
import dearpygui.dearpygui as dpg

from audio.audio_route import AudioRouter
import constants
from launchpad.route import LaunchpadReceiver
from project.project import Project
from ui.main_ui import Window
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
        self._draw_info(proj)

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
