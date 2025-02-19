import abc
from typing import Callable, Optional
import pygame
import pygame._sdl2.video

from launchpad.base import Launchpad
from lighting.lightmanager import LightManager, LightReceiver
from ptypes import int2, int3, int4
from singleton import singleton
from utils.color import col

pygame.init()
pygame.font.init()


@singleton
class WindowManager:
    def __init__(self) -> None:
        self._active_windows: list[Window] = []
        self._running: bool = True

    def open(self, *windows: "Window", show: bool = True) -> None:
        for w in windows:
            self._active_windows.append(w)

            if show:
                w.show()

    def close(self, window: "type[Window]") -> None:
        sel_windows = [w for w in self._active_windows if isinstance(w, window)]

        for sw in sel_windows:
            sw.hide()
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
            data = e.dict

            w = self._get_window(data.get("window", None))
            if w is None:
                continue

            if e.type == pygame.WINDOWCLOSE:
                self.close(Window)
                self._running = False
            elif e.type == pygame.MOUSEMOTION:
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

    def all(
        self, check: "Callable[[Window], bool]", action: "Callable[[Window], None]"
    ) -> None:
        for i in self._active_windows:
            if check(i):
                action(i)

    def show(self, arg: "type[Window] | Callable[[Window], bool]") -> None:
        if isinstance(arg, type):

            def check(w: Window):
                return isinstance(w, arg)

        else:
            check = lambda w: arg(w)

        self.all(check, lambda w: w.show())

    def hide(self, arg: "type[Window] | Callable[[Window], bool]") -> None:
        if isinstance(arg, type):

            def check(w: Window):
                return isinstance(w, arg)

        else:
            check = lambda w: arg(w)

        self.all(check, lambda w: w.hide())


type FontIdentifier = tuple[str, int, bool, bool]
type FontSpec = tuple[str, col]


class Window(abc.ABC):
    @staticmethod
    def background() -> col:
        return col.hex(0x1E1E1E)

    @staticmethod
    def title(name: str) -> str:
        return "CC/v2 - " + name

    def __init__(self, title: str, w: int, h: int, dx: int = 0, dy: int = 0) -> None:
        self._win = pygame._sdl2.video.Window(title, size=(w, h), hidden=True)
        self._win.resizable = False

        self._move(dx, dy)

        self._ren = pygame._sdl2.video.Renderer(self._win)
        self._surface = self._ren.to_surface()

    def render(
        self, specs: FontSpec, font: FontIdentifier, antialias: bool = True
    ) -> pygame.Surface:
        return pygame.font.SysFont(*font).render(
            specs[0],
            antialias,
            specs[1].rgb,
        )

    def _move(self, dx: int, dy: int) -> None:
        p = self._win.position

        if isinstance(p, int):
            self._win.position = (p + dx, p + dy)
        else:
            self._win.position = (p[0] + dx, p[1] + dy)  # type: ignore

    def show(self) -> None:
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

    def hide(self) -> None:
        self._win.hide()


class LaunchpadWindow(Window, LightReceiver):
    WIDTH = 25
    SPACE = 3
    PADD = 5

    CENTER_COL = col.hex(0xCCCCCC)
    CTRLLR_COL = col.hex(0x303030)
    WHITE = col.hex(0xFFFFFF)

    def __init__(self) -> None:
        w = self.WIDTH * 10 + self.SPACE * 9 + self.PADD * 2
        h = self.WIDTH * 10 + self.SPACE * 10 + self.PADD * 2

        super().__init__(self.title("Launchpad"), w, h)

        self._buttons: dict[int2, col] = {}

        self._button_hover: Optional[int2] = None

        LightManager().add_light_receiver(self)

    @property
    def buttons(self) -> dict[int2, col]:
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

    def frame(self) -> None:
        self._surface.fill(self.background().rgb)

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

        c = self.CENTER_COL if center else self.CTRLLR_COL
        bcol = self._buttons.get((x, y), None)

        if bcol:
            c = bcol

        if self._button_hover == (x, y):
            c.mix(self.WHITE)

        self._draw_rect(c, pos, brad, center)

    def _draw_rect(
        self,
        col: col,
        pos: int4,
        brad: int,
        center: bool,
    ) -> None:
        pygame.draw.rect(
            self._surface,
            col.rgb,
            pos,
            border_radius=brad,
        )

        pygame.draw.rect(
            self._surface,
            self.CTRLLR_COL.rgb if center else self.CENTER_COL.rgb,
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

    def __setitem__(self, pos: int2, c: col) -> None:
        p = (pos[0] + 1, pos[1] + 1)
        if c == col(0, 0, 0):
            del self._buttons[p]
            return

        self._buttons[p] = c

    def mouse_move(self, pos: int2, rel: int2, buttons: int3) -> None:
        self._button_hover = self._check_collision(*pos)

    def mouse_down(self, pos: int2, button: int) -> None:
        btn = self._check_collision(*pos)
        if btn:
            Launchpad.simulate_down(btn[0] - 1, btn[1] - 1)

    def mouse_up(self, pos: int2, button: int) -> None:
        btn = self._check_collision(*pos)
        if btn:
            Launchpad.simulate_up(btn[0] - 1, btn[1] - 1)


def open_and_run() -> int:
    from ui.track_ui import TrackWindow
    from ui.category_ui import CategoryUi
    from ui.generator_ui import GeneratorWindow

    man = WindowManager()
    man.open(
        LaunchpadWindow(),
        TrackWindow(),
        CategoryUi(),
    )
    man.open(
        GeneratorWindow(),
        show=False,
    )

    try:
        man.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        man.close(Window)

    return 0
