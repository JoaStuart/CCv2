import sys
from threading import Timer
import threading
import time

from daemon_thread import DaemonThread
from launchpad.base import Launchpad
import argparse

from lighting.keyframes import Keyframes
from lighting.lightmanager import LightManager
from lighting.lightmap import Lightmap
import logger
from project.project import Project
from scripts.lightmap import create_lightmap
from ui.main_ui import open_and_run


def main() -> int:
    parser = argparse.ArgumentParser("CC/v2", description="CoverCreator version 2")
    parser.add_argument("--lightmap", "-l", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("file", nargs="?")

    args = parser.parse_args(sys.argv[1:])

    logger.init(args.verbose)

    if args.lightmap:
        create_lightmap()
        sys.exit(0)

    # Open and load thigns
    Lightmap.load_all()
    Keyframes.load_internal()
    Launchpad.open_all()
    Launchpad.broadcast_clear()

    # Load project
    if args.file:
        load_finish = threading.Event()
        LightManager().play_raw(
            Keyframes.FRAME_CACHE["__loading"].persistent(load_finish)
        )

        Project.load(args.file)

        load_finish.set()

    LightManager().play_raw(Keyframes.FRAME_CACHE["__splash_entry"]).wait()

    Launchpad.resume_read()

    return open_and_run()


if __name__ == "__main__":
    try:
        code = main()  # Run application
    except KeyboardInterrupt:
        code = -1
        logger.info("Got keyboard interrupt, stopping app...")

    logger.info("Stopping daemon threads...")
    DaemonThread.clean_all()  # Stop daemon threads
    Launchpad.broadcast_clear()
    logger.info("----- End of output -----")
    sys.exit(code)  # Exit application
