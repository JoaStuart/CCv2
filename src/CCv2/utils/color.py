from typing import Callable

from ptypes import int3


type operand = int | float | col


class col:
    @staticmethod
    def hex(c: int) -> "col":
        return col((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)

    @staticmethod
    def rep(c: int) -> "col":
        return col(c, c, c)

    def __init__(self, r: int, g: int, b: int) -> None:
        self.r = r
        self.g = g
        self.b = b
        self._limit()

    def mix(self, other: operand) -> "col":
        return self._all(lambda a, b: (a + b) / 2, other)

    def gamma(self, other: float) -> "col":
        return self._all(lambda a, b: a * b, other)

    def dot(self) -> float:
        return (self.r + self.g + self.b) / 3

    def _limit(self) -> None:
        self.r = min(max(0, self.r), 255)
        self.g = min(max(0, self.g), 255)
        self.b = min(max(0, self.b), 255)

    @property
    def rgb(self) -> int3:
        return self.r, self.g, self.b

    def _all(self, op: Callable[[int, int | float], float], other: operand) -> "col":
        if isinstance(other, col):
            return col(
                round(op(self.r, other.r)),
                round(op(self.g, other.g)),
                round(op(self.b, other.b)),
            )
        return col(
            round(op(self.r, other)),
            round(op(self.g, other)),
            round(op(self.b, other)),
        )

    def _self(self, op: Callable[[int, int | float], float], other: operand) -> None:
        if isinstance(other, col):
            self.r = round(op(self.r, other.r))
            self.g = round(op(self.g, other.g))
            self.b = round(op(self.b, other.b))
        else:
            self.r = round(op(self.r, other))
            self.g = round(op(self.g, other))
            self.b = round(op(self.b, other))

        self._limit()

    def __str__(self) -> str:
        return f"col({self.r}, {self.g}, {self.b})"

    def __add__(self, other: operand) -> "col":
        return self._all(lambda a, b: a + b, other)

    def __sub__(self, other: operand) -> "col":
        return self._all(lambda a, b: a - b, other)

    def __mul__(self, other: operand) -> "col":
        return self._all(lambda a, b: a * b, other)

    def __truediv__(self, other: operand) -> "col":
        return self._all(lambda a, b: a / b, other)

    def __floordiv__(self, other: operand) -> "col":
        return self._all(lambda a, b: a // b, other)

    def __mod__(self, other: operand) -> "col":
        return self._all(lambda a, b: a % b, other)

    def __pow__(self, other: operand) -> "col":
        return self._all(lambda a, b: a**b, other)

    def __radd__(self, other: operand) -> "col":
        return self._all(lambda a, b: b + a, other)

    def __rsub__(self, other: operand) -> "col":
        return self._all(lambda a, b: b - a, other)

    def __rmul__(self, other: operand) -> "col":
        return self._all(lambda a, b: b * a, other)

    def __rtruediv__(self, other: operand) -> "col":
        return self._all(lambda a, b: b / a, other)

    def __rfloordiv__(self, other: operand) -> "col":
        return self._all(lambda a, b: b // a, other)

    def __rmod__(self, other: operand) -> "col":
        return self._all(lambda a, b: b % a, other)

    def __rpow__(self, other: operand) -> "col":
        return self._all(lambda a, b: b**a, other)

    def __iadd__(self, other: operand) -> None:
        self._self(lambda a, b: a + b, other)

    def __isub__(self, other: operand) -> None:
        self._self(lambda a, b: a - b, other)

    def __imul__(self, other: operand) -> None:
        self._self(lambda a, b: a * b, other)

    def __itruediv__(self, other: operand) -> None:
        self._self(lambda a, b: a / b, other)

    def __ifloordiv__(self, other: operand) -> None:
        self._self(lambda a, b: a // b, other)

    def __imod__(self, other: operand) -> None:
        self._self(lambda a, b: a % b, other)

    def __ipow__(self, other: operand) -> None:
        self._self(lambda a, b: a**b, other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, col):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False
