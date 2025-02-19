from ui.main_ui import Window, int3


class TrackWindow(Window):
    def __init__(self) -> None:
        super().__init__(self.title("Track"), 400, 70, dy=300)

    def frame(self) -> None:
        self._surface.fill(self.background().rgb)

    def mouse_move(
        self, pos: tuple[int, int], rel: tuple[int, int], buttons: int3
    ) -> None:
        return super().mouse_move(pos, rel, buttons)

    def mouse_down(self, pos: tuple[int, int], button: int) -> None:
        return super().mouse_down(pos, button)

    def mouse_up(self, pos: tuple[int, int], button: int) -> None:
        return super().mouse_up(pos, button)
