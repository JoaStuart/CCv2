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


from ..launchpad.base import Launchpad, LaunchpadIn, LaunchpadOut


class LaunchpadMk3Mini(Launchpad):
    @staticmethod
    def name_re() -> str:
        return r"LPMiniMK3 MI"

    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        if mode <= self.NOTE_ON + 0xF:
            if midi >= 0x24 and midi <= 0x43:  # Left side notes
                return midi % 4, 17 - midi // 4 - 1

            if midi >= 0x44 and midi <= 0x63:  # Right side notes
                return midi % 4 + 4, 25 - midi // 4 - 1

            if midi >= 0x64 and midi <= 0x6B:  # Right side register
                return 8, midi - 0x64

        else:  # ControlChange
            if midi >= 0x0A and midi <= 0x63:
                return midi % 10 - 1, 9 - midi // 10 - 1

        if midi < 99:
            return midi % 10 - 1, 9 - midi // 10 - 1
        return midi - 104, -1

    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        x, y = xy

        if y == -1:
            return 90 + x + 1, mode + self.CC_ON - self.NOTE_ON
        elif y >= 0 and y <= 7:
            if x == 8:  # Right register
                return 100 + y, mode
            elif x < 4:
                return 68 - 4 * y + (x - 4), mode
            else:
                return (96 - (4 * y)) + (x - 4), mode
        else:
            return 0, mode

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
                0x0D,
                0x00,
                0x7E,
                0xF7,
            ],  # Change to USER1 mode
        ]


class LaunchpadMk3MiniIn(LaunchpadMk3Mini, LaunchpadIn):
    pass


class LaunchpadMk3MiniOut(LaunchpadMk3Mini, LaunchpadOut):
    pass
