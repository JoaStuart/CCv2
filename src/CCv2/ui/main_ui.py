import abc
from typing import Optional
import pygame
import pygame._sdl2.video

from launchpad.base import Launchpad
from lighting.lightmanager import LightManager, LightReceiver
from lighting.lightmap import Lightmap
from singleton import singleton

pygame.init()


type int2 = tuple[int, int]
type int3 = tuple[int, int, int]
type int4 = tuple[int, int, int, int]


@singleton
class WindowManager:
    def __init__(self) -> None:
        self._active_windows: list[Window] = []
        self._running: bool = True

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
        clock = pygame.time.Clock()

        while self._running:
            self._eventloop()

            for w in self._active_windows:
                w.frame()
                w.present()

            clock.tick(60)

    def _eventloop(self) -> None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.close(Window)
                self._running = False
                continue

            data = e.dict

            w = self._get_window(data.get("window", None))
            if w is None:
                continue

            if e.type == pygame.MOUSEMOTION:
                w.mouse_move(data["pos"], data["rel"], data["buttons"])

            elif e.type == pygame.MOUSEBUTTONDOWN:
                w.mouse_down(data["pos"], data["button"])

            elif e.type == pygame.MOUSEBUTTONUP:
                w.mouse_up(data["pos"], data["button"])

    def _get_window(self, window: pygame._sdl2.video.Window) -> "Optional[Window]":
        for w in self._active_windows:
            if w.window == window:
                return w

        return None


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

    @property
    def window(self) -> pygame._sdl2.video.Window:
        return self._win

    @abc.abstractmethod
    def frame(self) -> None:
        pass

    @abc.abstractmethod
    def mouse_move(
        self,
        pos: int2,
        rel: int2,
        buttons: int3,
    ) -> None:
        pass

    @abc.abstractmethod
    def mouse_down(self, pos: int2, button: int) -> None:
        pass

    @abc.abstractmethod
    def mouse_up(self, pos: int2, button: int) -> None:
        pass

    def present(self) -> None:
        pygame._sdl2.Texture.from_surface(self._ren, self._surface).draw()
        self._ren.present()

    def close(self) -> None:
        self._win.hide()


def hexcol(c: int) -> int3:
    return (c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF


class LaunchpadWindow(Window, LightReceiver):
    WIDTH = 25
    SPACE = 3
    PADD = 5

    CENTER_COL = hexcol(0xCCCCCC)
    CTRLLR_COL = hexcol(0x303030)
    WHITE = hexcol(0xFFFFFF)

    def __init__(self, parent: Optional[pygame._sdl2.Window] = None) -> None:
        w = self.WIDTH * 10 + self.SPACE * 9 + self.PADD * 2
        h = self.WIDTH * 10 + self.SPACE * 10 + self.PADD * 2

        super().__init__("CC/v2 - Launchpad", w, h, parent)

        self._buttons: dict[int2, int3] = {}

        m = Lightmap.MAPS.get("Mk2+", None)
        if not m:
            raise RuntimeError("Could not find requested lightmap!")
        self._lightmap: Lightmap = m
        self._button_hover: Optional[int2] = None

        LightManager().add_light_receiver(self)

    @property
    def buttons(self) -> dict[int2, int3]:
        return self._buttons

    def _button_size(self, x: int, y: int) -> int2:
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

    def _button_move(self, x: int, y: int) -> int2:
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

    def _colmix(self, a: int3, b: int3) -> int3:
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

                self._draw_key(x, y)

    def _button_position(self, x: int, y: int) -> int4:
        mx, my = self._button_move(x, y)
        w, h = self._button_size(x, y)

        return (
            x * (self.WIDTH + self.SPACE) + self.PADD + mx,
            y * (self.WIDTH + self.SPACE) + self.PADD + my,
            w,
            h,
        )

    def _draw_key(self, x: int, y: int) -> None:
        pos = self._button_position(x, y)
        center = self._button_center(x, y)
        brad = 1 if center else 3

        col = self.CENTER_COL if center else self.CTRLLR_COL
        bcol = self._buttons.get((x, y), None)

        if bcol:
            col = bcol

        if self._button_hover == (x, y):
            col = self._colmix(col, self.WHITE)

        self._draw_rect(col, pos, brad, center)

    def _draw_rect(
        self,
        col: int3,
        pos: int4,
        brad: int,
        center: bool,
    ) -> None:
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

    def _check_collision(self, ux: int, uy: int) -> Optional[int2]:
        for x in range(10):
            for y in range(11):
                pos = self._button_position(x, y)

                if ux < pos[0] or ux > pos[0] + pos[2]:
                    continue

                if uy < pos[1] or uy > pos[1] + pos[3]:
                    continue

                return (x, y)

        return None

    def __setitem__(self, pos: int2, col: int) -> None:
        p = (pos[0] + 1, pos[1] + 1)
        if col == 0:
            del self._buttons[p]
            return

        self._buttons[p] = self._lightmap[col]

    def mouse_move(self, pos: int2, rel: int2, buttons: int3) -> None:
        self._button_hover = self._check_collision(*pos)

    def mouse_down(self, pos: int2, button: int) -> None:
        btn = self._check_collision(*pos)
        if btn:
            Launchpad.simulate_down(*btn)

    def mouse_up(self, pos: int2, button: int) -> None:
        btn = self._check_collision(*pos)
        if btn:
            Launchpad.simulate_up(*btn)


def open_and_run() -> int:
    man = WindowManager()
    man.open(LaunchpadWindow())

    try:
        man.mainloop()
    except KeyboardInterrupt:
        pass

    return 0
