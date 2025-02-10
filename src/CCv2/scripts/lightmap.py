import os
import pyautogui

import constants
from lightmap import Lightmap


def create_lightmap() -> None:
    name = input("Name of the new Lightmap: ")

    input("Move your mouse to the top-left color of the first grid and press [ENTER]")
    left_top = pyautogui.position()

    input(
        "Move your mouse to the bottom-right color of the first grid and press [ENTER]"
    )
    left_bottom = pyautogui.position()

    input("Move your mouse to the top-left color of the second grid and press [ENTER]")
    right_top = pyautogui.position()

    input(
        "Move your mouse to the bottom-right color of the second grid and press [ENTER]"
    )
    right_bottom = pyautogui.position()

    lightmap = Lightmap(name.strip())

    left_dist_x = left_bottom.x - left_top.x
    left_dist_y = left_bottom.y - left_top.y
    _get_colors(lightmap, left_top, left_dist_x, left_dist_y)

    right_dist_x = right_bottom.x - right_top.x
    right_dist_y = right_bottom.y - right_top.y
    _get_colors(lightmap, right_top, right_dist_x, right_dist_y, 0x40)

    with open(os.path.join(constants.LIGHTMAPS, name), "wb") as wf:
        wf.write(Lightmap.versions()[-1].dump(lightmap))


def _get_colors(
    lightmap: Lightmap, top: pyautogui.Point, dist_x: int, dist_y: int, start: int = 0
) -> None:
    for i in range(8):
        for j in range(8):
            rgb = pyautogui.pixel(
                int(top.x + (dist_x / 8) * i),
                int(top.y + (dist_y / 8) * j),
            )

            lightmap[start + i + j * 8] = rgb
