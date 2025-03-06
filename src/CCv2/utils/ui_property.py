from typing import Callable


class UiProperty[_T](property):
    def __init__(self, default: _T):
        self._value = default
        self._listeners: list[Callable[[_T], None]] = []

    @property
    def v(self) -> _T:
        return self._value

    @v.setter
    def v(self, target: _T) -> None:
        self._value = target

        self.change()

    def change(self) -> None:
        for l in self._listeners:
            l(self._value)

    def add_listener(self, listener: Callable[[_T], None]) -> int:
        self._listeners.append(listener)
        return len(self._listeners) - 1

    def remove_listener(
        self, listener: Callable[[_T], None] | None = None, index: int | None = None
    ) -> None:
        if listener is not None:
            self._listeners.remove(listener)
        elif index is not None:
            self._listeners.pop(index)

    def __str__(self) -> str:
        return str(self.v)
