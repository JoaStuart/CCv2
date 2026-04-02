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

from .base import Launchpad, LaunchpadIn, LaunchpadOut


class LaunchpadMk2(Launchpad):
    @staticmethod
    def name_re() -> str:
        return r"Launchpad MK2"

    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        if mode <= self.NOTE_ON + 0xF:
            return (midi % 10) - 1, 8 - (midi // 10)

        else:  # ControlChange
            return midi - 104, -1

    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        x, y = xy

        if y == -1:
            return 104 + x, mode + self.CC_ON - self.NOTE_ON
        else:
            return (8 - y) * 10 + x + 1, mode

    def lightmap(self) -> str:
        return "Mk2+Realism"

    def check_bounds(self, pos: tuple[int, int]) -> bool:
        return pos[0] >= 0 and pos[0] <= 8 and pos[1] >= -1 and pos[1] <= 7

    def clear_button(self) -> tuple[int, int]:
        return 0, -1

    def _welcome_messages(self) -> list[list[int]]:
        return [
            [
                0xF0,
                0x00,
                0x20,
                0x29,
                0x02,
                0x0E,
                0x00,
                0x14,
                0x00,
                0x00,
                0xF7,
            ],  # Change to USER1 mode
        ]


class LaunchpadMk2In(LaunchpadMk2, LaunchpadIn):
    pass


class LaunchpadMk2Out(LaunchpadMk2, LaunchpadOut):
    pass
