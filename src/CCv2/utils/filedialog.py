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
