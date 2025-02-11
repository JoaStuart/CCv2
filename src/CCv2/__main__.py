import sys
from daemon_thread import DaemonThread
from launchpad.base import Launchpad
import argparse

from lighting.keyframes import Keyframes
from lighting.lightmap import Lightmap
import logger
from scripts.lightmap import create_lightmap
from ui.main_ui import open_and_run


def main() -> int:
    parser = argparse.ArgumentParser("CC/v2", description="CoverCreator version 2")
    parser.add_argument("--lightmap", "-l", action="store_true")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args(sys.argv[1:])

    logger.init(args.verbose)

    if args.lightmap:
        create_lightmap()
        sys.exit(0)

    # Open and load thigns
    Lightmap.load_all()
    Launchpad.open_all()
    Keyframes.load_internal()

    return open_and_run()


if __name__ == "__main__":
    code = main()  # Run application

    logger.info("Stopping daemon threads...")
    DaemonThread.clean_all()  # Stop daemon threads
    Launchpad.broadcast_clear()
    logger.info("----- End of output -----")
    sys.exit(code)  # Exit application
