from ..launchpad.base import Launchpad, LaunchpadIn, LaunchpadOut


class LaunchpadClassic(Launchpad):
    @staticmethod
    def name_re() -> str:
        return r"Launchpad MIDI"

    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        if mode <= self.NOTE_ON + 0xF:
            if midi >= 0x24 and midi <= 0x43:  # Left side notes
                return midi % 4, 17 - midi // 4 - 1

            if midi >= 0x44 and midi <= 0x63:  # Right side notes
                return midi % 4 + 4, 25 - midi // 4 - 1

            if midi >= 0x64 and midi <= 0x6B:  # Right side register
                return 8, midi - 0x64

        else:  # ControlChange
            if midi >= 0x5A and midi <= 0x62:
                return midi % 10 - 1, 9 - midi // 10 - 1

        if midi < 99:
            return midi % 10 - 1, 9 - midi // 10 - 1
        return midi - 104, -1

    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        x, y = xy

        if y == -1:
            return 0x68 + x, mode + self.CC_ON - self.NOTE_ON
        elif y >= 0 and y <= 7:
            if x == 8:  # Right register
                return 100 + y, mode
            elif x < 4:
                return 68 - 4 * y + (x - 4), mode
            else:
                return (96 - (4 * y)) + (x - 4), mode
        else:
            return 0, mode

    def check_bounds(self, pos: tuple[int, int]) -> bool:
        return pos[0] >= 0 and pos[0] <= 8 and pos[1] >= -1 and pos[1] <= 7

    def lightmap(self) -> str:
        return "ClassicMiniS"

    def clear_button(self) -> tuple[int, int]:
        return 0, -1

    def _welcome_messages(self) -> list[list[int]]:
        return [
            [
                0xB0,
                0x00,
                0x02,
            ],  # Change to USER1 mode
        ]


class LaunchpadClassicIn(LaunchpadClassic, LaunchpadIn):
    pass


class LaunchpadClassicOut(LaunchpadClassic, LaunchpadOut):
    pass
