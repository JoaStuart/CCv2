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

import json
import os
import struct
import zipfile


def zip_dir(zfile: zipfile.ZipFile, root: str, arcname: str = "") -> None:
    if len(arcname) > 0:
        zfile.mkdir(arcname)

    for f in os.listdir(root):
        af = os.path.join(root, f)

        if os.path.isfile(af):
            print(f"Compressing {f}...")
            zfile.write(af, arcname + f)
        else:
            print(f"Iterating {f}...")
            zip_dir(zfile, af, arcname + f + "/")


def convert_savefile(_args: list[str]) -> int:
    out_file = input("Path of `out.txt` > ").strip()
    if not os.path.isfile(out_file):
        print("File not found!")
        return 1

    cache_dir = input("Path to CCv2's cache directory > ").strip()
    if not os.path.isdir(cache_dir):
        print("Cache dir not found!")
        return 1

    cache_pages = os.path.join(cache_dir, "pages")
    cache_audio = os.path.join(cache_dir, "audio")
    cache_keyframes = os.path.join(cache_dir, "keyframes")

    for fdir in [cache_pages, cache_audio, cache_keyframes]:
        os.makedirs(fdir, exist_ok=True)
        for file in os.listdir(fdir):
            os.remove(os.path.join(fdir, file))

    with open(out_file, "r") as rf:
        identifier = rf.readline().strip()

        title = rf.readline().strip()
        audio = rf.readline().strip()
        _audio_frontend = rf.readline().strip()
        buttons = rf.readline().strip()
        lights = rf.readline().strip()
        keyframes = rf.readline().strip()

    audio_file = input(f"Path to the file `{audio}` > ")
    if not os.path.isfile(audio_file):
        print("Audio file not found!")
        return 1
    audio_name = audio_file.replace("\\", "/").split("/")[-1]

    with open(audio_file, "rb") as rf:
        with open(os.path.join(cache_audio, audio_name), "wb") as wf:
            wf.write(rf.read())

    btn = eval(buttons)
    lgts = eval(lights)
    kf = eval(keyframes)

    ver = float(identifier[5:-1])
    if ver > 1.1:
        print(
            "Not all features of LPC V1.2 are supported yet. Expect direct-bound sound samples, direct-bound light keyframes and wormhole not to work!"
        )

    elif ver > 1.0:
        print(
            "Not all features of LPC V1.1 are supported yet. Expect direct-bound sound samples and direct-bound light keyframes not to work!"
        )

    exp_pages = []

    for p in range(len(btn)):
        buff = []
        for k in range(len(btn[p])):
            k = btn[p][k][:3]

            if not isinstance(k[0], float):
                continue

            packed_pos = (k[1] << 4) | k[2]
            buff.append(struct.pack("fB", k[0], packed_pos))

        if len(buff) > 0:
            with open(os.path.join(cache_pages, f"{p}.lpb"), "wb") as wf:
                wf.write(b"".join(buff))

            exp_pages.append(p)

    lgts_buff = []
    for l in lgts:
        time = l[0]
        name = l[1]
        duration = l[2]
        offx = l[3]
        offy = l[4]
        clear = l[5]

        lgts_buff.append(
            struct.pack(
                "ffbbI",
                time,
                duration if clear else -duration,
                offx - 1,
                offy - 1,
                len(name),
            )
        )
        lgts_buff.append(name.encode())

    with open(os.path.join(cache_pages, "lights.lpl"), "wb") as wf:
        wf.write(b"".join(lgts_buff))

    notify_different_channels = False

    for name, frames in kf.items():
        buff = [b"\xcc\x01"]

        buff.append(struct.pack("fI", 0.3, len(frames)))

        for f in frames:
            buff.append(struct.pack("I", len(f)))

            for pos, rgb in f.items():
                packed_pos = ((pos[0] + 1) << 4) | (pos[1] + 1)

                if rgb[0] < 0 or rgb[1] < 0 or rgb[2] < 0:
                    if not notify_different_channels:
                        print(
                            "Expect lights on different channels like flashing to be replaced!"
                        )
                        notify_different_channels = True

                    rgb = (255, 255, 255)

                buff.append(struct.pack("BBBB", packed_pos, *rgb))

        with open(os.path.join(cache_keyframes, f"{name}.lpk"), "wb") as wf:
            wf.write(b"".join(buff))

    with open(os.path.join(cache_dir, "project.lpj"), "w") as wf:
        wf.write(
            json.dumps(
                {
                    "$schema": "../internal/schemas/project_v1.json",
                    "title": title,
                    "pages": {"buttons": exp_pages},
                }
            )
        )

    out_file = input("Output file name > ").strip()

    with zipfile.ZipFile(
        out_file, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5
    ) as zfile:
        zip_dir(zfile, cache_dir)

    print("Converted LPC cover successfully!")
    return 0
