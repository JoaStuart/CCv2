import pygame
import pygame.draw_py
from launchpad.base import Launchpad
from lighting.lightmap import Lightmap
from ptypes import int2, int3
from ui.main_ui import Window


class GeneratorWindow(Window):
    WIDTH = 20
    SPACING = 3

    def __init__(self) -> None:
        total_width = 16 * self.WIDTH + 14 * self.SPACING + self.WIDTH

        super().__init__(self.title("Generator"), total_width, 500, dx=-500)

    def _get_primary_lightmap(self) -> Lightmap:
        if len(Launchpad.OUTPUTS) == 0:
            return Lightmap.MAPS["Mk2+Realism"]

        return Lightmap.MAPS[Launchpad.OUTPUTS[0].lightmap()]

    def frame(self) -> None:
        self._surface.fill(self.background().rgb)

        self._draw_colors()

    def _draw_colors(self) -> None:
        lm = self._get_primary_lightmap()

        for i in range(2):
            for x in range(8):
                for y in range(8):
                    left = 8 * self.WIDTH + 7 * self.SPACING + self.WIDTH

                    pygame.draw.rect(
                        self._surface,
                        lm[i * 64 + y * 8 + x].gamma(2).rgb,
                        (
                            i * left + x * self.WIDTH + x * self.SPACING,
                            y * self.WIDTH + y * self.SPACING,
                            self.WIDTH,
                            self.WIDTH,
                        ),
                        border_radius=2,
                    )

    def mouse_move(self, pos: int2, rel: int2, buttons: int3) -> None:
        return super().mouse_move(pos, rel, buttons)

    def mouse_down(self, pos: int2, button: int) -> None:
        return super().mouse_down(pos, button)

    def mouse_up(self, pos: int2, button: int) -> None:
        return super().mouse_up(pos, button)
