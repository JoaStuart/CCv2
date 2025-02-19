import os
from typing import Callable

import pygame
import constants
from launchpad.route import LaunchpadReceiver
from lighting.generator import Generator
from ptypes import int2, int3
from ui.generator_ui import GeneratorWindow
from ui.main_ui import LaunchpadWindow, Window, WindowManager
from ui.track_ui import TrackWindow
from utils.color import col


class CategoryUi(Window):
    WIDTH = 70

    FOREGROUND = col.hex(0xCCCCCC)

    def __init__(self) -> None:
        self._category_names = ["Play", "Generate"]

        super().__init__(
            self.title("Modes"),
            self.WIDTH * len(self._category_names)
            + 1 * (len(self._category_names) - 1),
            self.WIDTH,
            dy=-300,
        )

        self._category_texts = [
            self.render(
                (n, self.FOREGROUND),
                ("Segoe UI", 15, False, False),
            )
            for n in self._category_names
        ]

        category_icons = ["play.png", "generator.png"]

        self._category_icons = [
            pygame.image.load(os.path.join(constants.INTERNAL_ICONS, i))
            for i in category_icons
        ]

        self._category_switch: list[Callable[[], None]] = [
            self._switch_player,
            self._switch_generator,
        ]

        self._hover: int = -1

    def frame(self) -> None:
        self._surface.fill(self.background().rgb)

        for i in range(len(self._category_names)):
            txt = self._category_texts[i]
            ico = self._category_icons[i]

            txt_x = i * self.WIDTH + self.WIDTH // 2 - txt.get_width() // 2
            txt_y = (2 * self.WIDTH) // 3 - txt.get_height() // 2
            ico_x = i * self.WIDTH + self.WIDTH // 2 - ico.get_width() // 2
            ico_y = self.WIDTH // 3 - ico.get_height() // 2

            if self._hover == i:
                pygame.draw.rect(
                    self._surface,
                    col.hex(0x303030).rgb,
                    (i * self.WIDTH, 0, self.WIDTH, self.WIDTH),
                )

            self._surface.blit(txt, (txt_x, txt_y))
            self._surface.blit(ico, (ico_x, ico_y))

    def mouse_move(self, pos: int2, rel: int2, buttons: int3) -> None:
        if pos[0] == 0 or pos[1] == 0 or pos[1] == self.WIDTH - 1:
            self._hover = -1
            return

        self._hover = pos[0] // self.WIDTH

        if self._hover >= len(self._category_names):
            self._hover = -1

    def mouse_down(self, pos: int2, button: int) -> None:
        if self._hover == -1:
            return

        self._category_switch[self._hover]()

    def mouse_up(self, pos: int2, button: int) -> None:
        return super().mouse_up(pos, button)

    def _switch_generator(self) -> None:
        LaunchpadReceiver.request_input(Generator())

        WindowManager().hide(lambda w: not isinstance(w, (CategoryUi, LaunchpadWindow)))
        WindowManager().show(GeneratorWindow)

    def _switch_player(self) -> None:
        WindowManager().hide(GeneratorWindow)
        WindowManager().show(TrackWindow)
