import abc
from typing import Optional
import pygame
import pygame._sdl2.video

from lighting.lightmanager import LightManager, LightReceiver
from lighting.lightmap import Lightmap
from singleton import singleton

pygame.init()


@singleton
class WindowManager:
    def __init__(self) -> None:
        self._active_windows: list[Window] = []

    def open(self, *windows: "Window") -> None:
        for w in windows:
            self._active_windows.append(w)
            w.open()

    def close(self, window: "type[Window]") -> None:
        sel_windows = [w for w in self._active_windows if isinstance(w, window)]

        for sw in sel_windows:
            sw.close()
            self._active_windows.remove(sw)

    def mainloop(self) -> None:
        running = True
        clock = pygame.time.Clock()

        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.close(Window)
                    running = False

            for w in self._active_windows:
                w.frame()
                w.present()

            clock.tick(60)


class Window(abc.ABC):
    def __init__(
        self, title: str, w: int, h: int, parent: Optional[pygame._sdl2.Window]
    ) -> None:
        self._win = pygame._sdl2.video.Window(title, size=(w, h))
        self._win.hide()
        if parent:
            self._win.set_modal_for(parent)

        self._ren = pygame._sdl2.video.Renderer(self._win)
        self._surface = self._ren.to_surface()

    def open(self) -> None:
        self._win.show()

    @abc.abstractmethod
    def frame(self) -> None:
        pass

    def present(self) -> None:
        pygame._sdl2.Texture.from_surface(self._ren, self._surface).draw()
        self._ren.present()

    def close(self) -> None:
        self._win.hide()


def hexcol(c: int) -> tuple[int, int, int]:
    return (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF


class LaunchpadWindow(Window, LightReceiver):
    WIDTH = 25
    SPACE = 3
    PADD = 5

    CENTER_COL = hexcol(0xCCCCCC)
    CTRLLR_COL = hexcol(0x303030)

    def __init__(self, parent: Optional[pygame._sdl2.Window] = None) -> None:
        w = self.WIDTH * 10 + self.SPACE * 9 + self.PADD * 2
        h = self.WIDTH * 10 + self.SPACE * 10 + self.PADD * 2

        super().__init__("CC/v2 - Launchpad", w, h, parent)

        self._buttons: dict[tuple[int, int], tuple[int, int, int]] = {}

        m = Lightmap.MAPS.get("Mk2+", None)
        if not m:
            raise RuntimeError("Could not find requested lightmap!")
        self._lightmap: Lightmap = m

        LightManager().add_light_receiver(self)

    @property
    def buttons(self) -> dict[tuple[int, int], tuple[int, int, int]]:
        return self._buttons

    def _button_size(self, x: int, y: int) -> tuple[int, int]:
        if x == 0 and y == 0:
            return self.WIDTH // 2, self.WIDTH // 2

        if y >= 9:
            return self.WIDTH, self.WIDTH // 2

        if x == 9 and y == 0:
            return self.WIDTH - 2, self.WIDTH - 2

        return self.WIDTH, self.WIDTH

    def _has_button(self, x: int, y: int) -> bool:
        if (x == 0 or x == 9) and y >= 9:
            return False

        return True

    def _button_move(self, x: int, y: int) -> tuple[int, int]:
        if x == 0 and y == 0:
            return self.WIDTH // 4, self.WIDTH // 4

        if y == 10:
            return 0, -self.WIDTH // 2

        if x == 9 and y == 0:
            return 1, 1

        return 0, 0

    def _button_center(self, x: int, y: int) -> bool:
        if x == 0 or x == 9 or y == 0 or y >= 9:
            return False

        return True

    def _colmix(
        self, a: tuple[int, int, int], b: tuple[int, int, int]
    ) -> tuple[int, int, int]:
        return (
            (a[0] + b[0]) // 2,
            (a[1] + b[1]) // 2,
            (a[2] + b[2]) // 2,
        )

    def frame(self) -> None:
        self._surface.fill((30, 30, 30))

        for x in range(10):
            for y in range(11):
                if not self._has_button(x, y):
                    continue

                w, h = self._button_size(x, y)
                mx, my = self._button_move(x, y)
                center = self._button_center(x, y)
                pos = (
                    x * (self.WIDTH + self.SPACE) + self.PADD + mx,
                    y * (self.WIDTH + self.SPACE) + self.PADD + my,
                    w,
                    h,
                )
                brad = 1 if center else 3

                col = self.CENTER_COL if center else self.CTRLLR_COL
                bcol = self._buttons.get((x, y), None)

                if bcol:
                    col = bcol

                pygame.draw.rect(
                    self._surface,
                    col,
                    pos,
                    border_radius=brad,
                )

                pygame.draw.rect(
                    self._surface,
                    self.CTRLLR_COL if center else self.CENTER_COL,
                    pos,
                    width=1,
                    border_radius=brad,
                )

    def __setitem__(self, pos: tuple[int, int], col: int) -> None:
        p = (pos[0] + 1, pos[1] + 1)
        if col == 0:
            del self._buttons[p]
            return

        self._buttons[p] = self._lightmap[col]


def open_and_run() -> int:
    man = WindowManager()
    man.open(LaunchpadWindow())

    try:
        man.mainloop()
    except KeyboardInterrupt:
        pass

    return 0
