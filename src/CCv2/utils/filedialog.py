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

import subprocess
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename


def select_file(title: str, filetype: tuple[str, str]) -> str | None:
    try:
        file_path = subprocess.check_output(
            [
                "zenity",
                "--file-selection",
                f"--file-filter={filetype[0]}|{filetype[1]}",
            ],
            text=True,
        ).strip()

    except subprocess.CalledProcessError:
        file_path = None

    except FileNotFoundError:
        root = Tk()
        root.withdraw()

        file_path = askopenfilename(title=title, filetypes=[filetype])

        root.destroy()

    return file_path if file_path else None


def select_save(title: str, filetype: tuple[str, str]) -> str | None:
    try:
        file_path = subprocess.check_output(
            [
                "zenity",
                "--file-selection",
                "--save",
                f"--file-filter={filetype[0]}|{filetype[1]}",
            ],
            text=True,
        ).strip()

    except subprocess.CalledProcessError:
        file_path = None

    except FileNotFoundError:
        root = Tk()
        root.withdraw()

        file_path = asksaveasfilename(title=title, filetypes=[filetype])

        root.destroy()

    return file_path if file_path else None
