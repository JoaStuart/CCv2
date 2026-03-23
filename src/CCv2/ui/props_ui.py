import dearpygui.dearpygui as dpg

from ..ptypes import int2
from ..singleton import singleton
from ..ui.main_ui import Window


@singleton
class PropsWindow(Window):
    BUTTON_PROPS = ["button_time", "button_pos"]
    LIGHT_PROPS = ["light_name", "light_duration", "light_persist", "light_move"]

    def __init__(self) -> None:
        super().__init__("Properties", "props")

    def position(self, full_size: int2, size: int2) -> int2:
        """Calculate the position this window should sit at.
        See super class `Window`
        """

        return full_size[0] - size[0], full_size[1] - size[1]

    def setup(self) -> None:
        """Setup the window"""

        self.main.disabled_theme()

        self._draw_button()
        dpg.add_spacer(height=20)
        dpg.add_separator()
        dpg.add_spacer(height=20)
        self._draw_light()

        self._disable_light()

    def _draw_button(self) -> None:
        """Draw informations about the currently selected button"""

        with dpg.group(horizontal=True):
            dpg.add_text("Button time (s):")
            dpg.add_input_float(
                format="%.2f",
                min_value=0,
                default_value=0,
                max_value=100,
                step=0.01,
                max_clamped=True,
                min_clamped=True,
                tag="button_time",
                enabled=False,
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Button pos:")
            dpg.add_input_intx(
                default_value=(0, 0),
                size=2,
                min_value=-1,
                max_value=9,
                min_clamped=True,
                max_clamped=True,
                tag="button_pos",
                enabled=False,
            )

    def _draw_light(self) -> None:
        """Draw information about the currently selected light"""

        with dpg.group(horizontal=True):
            dpg.add_text("Light name:")
            dpg.add_input_text(
                default_value="some_light", no_spaces=True, tag="light_name"
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Light duration (s):")
            dpg.add_input_float(
                default_value=0.3,
                min_clamped=True,
                min_value=0.1,
                step=0.05,
                format="%.2f",
                tag="light_duration",
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Light persist:")
            dpg.add_checkbox(
                default_value=False,
                tag="light_persist",
            )

        with dpg.group(horizontal=True):
            dpg.add_text("Light move:")
            dpg.add_input_intx(
                size=2,
                default_value=(0, 0),
                tag="light_move",
            )

    def _enable_btn(self) -> None:
        """Enable the button properties"""

        for k in self.BUTTON_PROPS:
            dpg.enable_item(k)

    def _disable_light(self) -> None:
        """Disable the light properties"""

        for k in self.LIGHT_PROPS:
            dpg.disable_item(k)

    def _enable_light(self) -> None:
        """Enable the light properties"""

        for k in self.LIGHT_PROPS:
            dpg.enable_item(k)

    def focus_button(self, t: float, pos: int2) -> None:
        """Focus on the given button

        Args:
            t (float): The timestamp of the button
            pos (int2): The position of the button
        """

        self._enable_btn()
        dpg.set_value("button_time", t)
        dpg.set_value("button_pos", pos)

    def unfocus_button(self) -> None:
        """Unfocus any focused button"""

        dpg.set_value("button_time", 0)
        dpg.set_value("button_pos", (0, 0))

        for k in self.BUTTON_PROPS:
            dpg.disable_item(k)
