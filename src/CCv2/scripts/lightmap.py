import os

import constants
from lighting.lightmap import Lightmap


def create_lightmap() -> None:
    name = input("Name of the new Lightmap: ")

    file = input("Where is the Kaskobi-Style palette stored?\n> ")

    with open(file, "r") as rf:
        palette = rf.read()

    lm = Lightmap(name.strip())

    for p in palette.split(";"):
        p = p.strip()

        if len(p) == 0:
            continue

        key, col = p.split(", ")

        ikey = int(key)
        pcol = col.split(" ")
        if len(pcol) != 3:
            continue

        icol = (
            int(pcol[0]),
            int(pcol[1]),
            int(pcol[2]),
        )

        lm[ikey] = icol

    ver = Lightmap.versions()[-1]

    with open(os.path.join(constants.LIGHTMAPS, name), "wb") as wf:
        wf.write(ver.dump(lm))
