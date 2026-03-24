import os

from ..utils.versioning import VersionLoader

from .. import constants
from ..lighting.lightmap import Lightmap
from ..utils.color import col


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
