# Copyright (C) 2026 JoaStuart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Callable

from ..ptypes import int3


type operand = int | float | col


class col:
    @staticmethod
    def hex(c: int) -> "col":
        """Turn a hex int to a color

        Args:
            c (int): The int representation of the color

        Returns:
            col: The color extracted from the given int
        """

        return col((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)

    @staticmethod
    def rep(c: int) -> "col":
        """Repeat the given value for all color components

        Args:
            c (int): The int to repeat

        Returns:
            col: The color resulting from this operation
        """

        return col(c, c, c)

    def __init__(self, r: int, g: int, b: int) -> None:
        """A color utility class

        Args:
            r (int): Red color channel
            g (int): Green color channel
            b (int): Blue color channel
        """

        self.r = r
        self.g = g
        self.b = b
        self._limit()

    def mix(self, other: operand) -> "col":
        """Mix the color with another

        Args:
            other (operand): The other operand to mix this color with

        Returns:
            col: The resulting color
        """

        return self._all(lambda a, b: (a + b) / 2, other)

    def gamma(self, other: float) -> "col":
        """Apply gamma filtering to the current color

        Args:
            other (float): The gamma value to change the color by

        Returns:
            col: The resulting color
        """

        return self._all(lambda a, b: a * b, other)

    def dot(self) -> float:
        """The dot product of the color

        Returns:
            float: The resulting value
        """

        return (self.r + self.g + self.b) / 3

    def _limit(self) -> None:
        """Limit the color to what a 8bit RGB color expects"""

        self.r = min(max(0, self.r), 255)
        self.g = min(max(0, self.g), 255)
        self.b = min(max(0, self.b), 255)

    @property
    def rgb(self) -> int3:
        """
        Returns:
            int3: The color as a tuple
        """

        return self.r, self.g, self.b

    @property
    def hsl(self) -> int3:
        """
        Returns:
            int3: The color in format hsl as a tuple (s & l as `0-100`)
        """

        r = self.r / 255
        g = self.g / 255
        b = self.b / 255

        mx = max(r, g, b)
        mn = min(r, g, b)
        delta = mx - mn

        L = (mx + mn) / 2

        if delta == 0:
            S = 0
        else:
            S = delta / (1 - abs(2 * L - 1))

        if delta == 0:
            H = 0
        elif mx == r:
            H = 60 * (((g - b) / delta) % 6)
        elif mx == g:
            H = 60 * (((b - r) / delta) + 2)
        elif mx == b:
            H = 60 * (((r - g) / delta) + 4)
        else:
            assert False

        return (int(H), int(S * 100), int(L * 100))

    def hsldist(self, other: col) -> int:
        dstcirc = lambda a, b: min(abs(a - b), abs(a - (b - 360)), abs(a - (b + 360)))

        sh, _, sl = self.hsl
        oh, _, ol = other.hsl

        return dstcirc(sh, oh) + abs(sl - ol) * 2

    def _all(self, op: Callable[[int, int | float], float], other: operand) -> "col":
        """Apply an operation to all the color components

        Args:
            op (Callable[[int, int  |  float], float]): The operation to perform
            other (operand): The operand to perform the operation with

        Returns:
            col: The resulting color
        """

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
        """Apply an operation to this color class

        Args:
            op (Callable[[int, int  |  float], float]): The operation to perform
            other (operand): The operand to perform the operation with
        """

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

    def __iadd__(self, other: operand) -> "col":
        return self._all(lambda a, b: a + b, other)

    def __isub__(self, other: operand) -> "col":
        return self._all(lambda a, b: a - b, other)

    def __imul__(self, other: operand) -> "col":
        return self._all(lambda a, b: a * b, other)

    def __itruediv__(self, other: operand) -> "col":
        return self._all(lambda a, b: a / b, other)

    def __ifloordiv__(self, other: operand) -> "col":
        return self._all(lambda a, b: a // b, other)

    def __imod__(self, other: operand) -> "col":
        return self._all(lambda a, b: a % b, other)

    def __ipow__(self, other: operand) -> "col":
        return self._all(lambda a, b: a**b, other)

    def __abs__(self) -> "col":
        return self._all(lambda a, _: abs(a), 0)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, col):
            return self.r == other.r and self.g == other.g and self.b == other.b
        return False
