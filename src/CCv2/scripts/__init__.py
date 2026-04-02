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

from .list_audio_devices import list_audio_devices
from .saveconvert import convert_savefile
from .lightmap import create_lightmap

SCRIPTS = [
    ("saveconvert", convert_savefile),
    ("lightmap", create_lightmap),
    ("listaudiodevices", list_audio_devices),
]
