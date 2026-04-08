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

import argparse
import heapq
import json
from typing import Optional

from ..ptypes import int3
from ..utils.color import col
from ..lighting.lightmap import Lightmap


def get_next_color(
    lightmap: Lightmap, lastdist: int, current: col, target: col
) -> Optional[tuple[int, col]]:
    color = None
    curdist = 0xFFFFFF
    vel = 0
    for i, c in lightmap.items():
        if (cdist := c.hsldist(current)) < curdist and c.hsldist(target) < lastdist:
            color = c
            curdist = cdist
            vel = i

    if color is None:
        return None

    return vel, color


def gradient_main(script_args: list[str]) -> int:
    Lightmap.load_all()

    parser = argparse.ArgumentParser(prog="python -m CCv2 --perfectgradient")
    parser.add_argument("--glightmap", required=True, choices=Lightmap.MAPS.keys())
    parser.add_argument("colpoint", nargs="+")

    args = parser.parse_args(script_args)
    lightmap = Lightmap.MAPS[args.glightmap]

    if len(args.colpoint) < 2:
        print("Not enough color points")
        return 1

    steps = []

    for i in range(len(args.colpoint) - 1):
        start = col.hex(int.from_bytes(bytes.fromhex(args.colpoint[i])))
        end = col.hex(int.from_bytes(bytes.fromhex(args.colpoint[i + 1])))

        svel = lightmap.closest(start)
        if i == 0:
            steps.append(svel)
        lastdist = lightmap[svel].hsldist(end)
        color = start

        while (c := get_next_color(lightmap, lastdist, color, end)) is not None:
            steps.append(c[0])
            color = c[1]
            lastdist = c[1].hsldist(end)

    print("|".join([json.dumps({"type": "gencol", "vel": s}) for s in steps]))

    return 0
