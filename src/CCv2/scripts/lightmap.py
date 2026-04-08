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

import os

from ..utils.versioning import VersionLoader

from .. import constants
from ..lighting.lightmap import Lightmap
from ..utils.color import col


def create_lightmap(_args) -> int:
    name = input("Name of the new Lightmap: ")

    file = input("Where is the Kaskobi-Style palette stored?\n> ")

    with open(file, "r") as rf:
        palette = rf.read()

    lm = Lightmap(name.strip())

    for p in palette.split(";"):
        p = p.strip()

        if len(p) == 0:
            continue

        key, c = p.split(", ")

        ikey = int(key)
        pcol = c.split(" ")
        if len(pcol) != 3:
            continue

        icol = col(
            int(pcol[0]),
            int(pcol[1]),
            int(pcol[2]),
        )

        lm[ikey] = icol

    VersionLoader.register_all()
    with open(os.path.join(constants.LIGHTMAPS, name), "wb") as wf:
        wf.write(VersionLoader.dump_best(Lightmap, lm))

    return 0
