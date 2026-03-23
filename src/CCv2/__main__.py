import os
import sys
import argparse
import time

from .utils.daemon_thread import DaemonThread
from .launchpad.base import Launchpad
from .lighting.keyframes import Keyframes
from .lighting.lightmap import Lightmap
from . import logger
from .project.project import Project
from .scripts import SCRIPTS
from .utils.animations import load_animation, splash_animation


def main() -> None:
    """Run the project"""

    parser = argparse.ArgumentParser("CC/v2", description="CoverCreator version 2")
    for n, _ in SCRIPTS:
        parser.add_argument(f"--{n}", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--oldui", action="store_true")
    parser.add_argument("--vpad", action="store_true")
    parser.add_argument("file", nargs="?")

    args = parser.parse_args(sys.argv[1:])

    logger.init(args.verbose)

    for name, script in SCRIPTS:
        if getattr(args, name):
            script()
            sys.exit(0)

    logger.debug("Clearing cache directory")
    Project.clear()

    # Open and load things
    Lightmap.load_all()
    Keyframes.load_internal()
    Launchpad.open_all()
    Launchpad.broadcast_clear()

    # Load project
    if args.file:
        logger.info("Loading project %s", args.file)
        load_finish = load_animation()

        Project.load(args.file)
        Project.CURRENT_PROJECT.v.bake()

        load_finish.set()

    splash_finish = splash_animation()

    Launchpad.resume_read()

    if args.oldui:
        from .ui.main_ui import open_and_run
    else:
        from .ui.web_ui import open_and_run

    open_and_run(splash_finish, args)


if __name__ == "__main__":
    try:
        main()  # Run application
    except KeyboardInterrupt:
        logger.info("Got keyboard interrupt, stopping app...")

    logger.info("Stopping daemon threads...")
    DaemonThread.clean_all()  # Stop daemon threads
    Launchpad.broadcast_clear()  # Clear launchpads
    logger.info("----- End of output -----")
    sys.exit(0)  # Exit application
