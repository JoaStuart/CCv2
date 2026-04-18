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

from typing import TYPE_CHECKING, Callable
import numpy as np

if TYPE_CHECKING:
    from .launchpad.midiio import MidiInput, MidiOutput


type int2 = tuple[int, int]
type int3 = tuple[int, int, int]
type int4 = tuple[int, int, int, int]


type AudioRaw = np.ndarray[tuple[int, int], np.dtype[np.int16]]


type MidiCallback = Callable[[list[int]], None]
type MidiInputOpen = "Callable[[MidiCallback], MidiInput]"
type MidiOutputOpen = "Callable[[], MidiOutput]"
