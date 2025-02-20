from launchpad.base import Launchpad, LaunchpadIn, LaunchpadOut


class LaunchpadMk3Pro(Launchpad):
    @staticmethod
    def name_re() -> str:
        return r"^LPProMK3 MIDI$"

    def midi_to_xy(self, midi: int, mode: int) -> tuple[int, int]:
        if mode <= self.NOTE_ON + 0xF:
            if midi >= 0x24 and midi <= 0x43:  # Left side notes
                return midi % 4, 17 - midi // 4 - 1

            if midi >= 0x44 and midi <= 0x63:  # Right side notes
                return midi % 4 + 4, 25 - midi // 4 - 1

            if midi >= 0x6C and midi <= 0x73:  # Left side register
                return -1, midi - 0x6C

            if midi >= 0x64 and midi <= 0x6B:  # Right side register
                return 8, midi - 0x64

            if midi >= 0x74 and midi <= 0x7B:  # Upper bottom row
                return midi - 0x74, 8

            if midi >= 0xC and midi <= 0x13:  # Lower bottom row
                return midi - 0xC, 9

        else:  # ControlChange
            if midi >= 0x0A and midi <= 0x63:
                return midi % 10 - 1, 9 - midi // 10 - 1

            if midi >= 0x65 and midi <= 0x6C:  # Upper bottom row CC
                return midi - 0x66, 8
            if midi >= 0x1 and midi <= 0x8:  # Lower bottom row CC
                return midi - 1, 8

        if midi < 99:
            return midi % 10 - 1, 9 - midi // 10 - 1
        return midi - 104, -1

    def xy_to_midi(self, xy: tuple[int, int], mode: int) -> tuple[int, int]:
        x, y = xy

        if y == -1:
            return 90 + x + 1, mode + self.CC_ON - self.NOTE_ON
        elif y >= 0 and y <= 7:
            if x == -1:  # Left register
                return 108 + y, mode
            elif x == 8:  # Right register
                return 100 + y, mode
            elif x < 4:
                return 68 - 4 * y + (x - 4), mode
            else:
                return (96 - (4 * y)) + (x - 4), mode
        elif y == 8:  # Upper bottom row
            return 116 + x, mode
        elif y == 9:  # Lower bottom row
            return 12 + x, mode
        else:
            return 0, mode

    def lightmap(self) -> str:
        return "Mk2+Realism"

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


class LaunchpadMk3ProIn(LaunchpadMk3Pro, LaunchpadIn):
    pass


class LaunchpadMk3ProOut(LaunchpadMk3Pro, LaunchpadOut):
    pass
