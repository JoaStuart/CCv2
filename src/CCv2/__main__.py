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

import sys
import argparse

from .audio import audio_route
from .utils.versioning import VersionLoader
from .utils.daemon_thread import DaemonThread
from .launchpad.base import Launchpad
from .lighting.keyframes import Keyframes
from .lighting.lightmap import Lightmap
from . import logger
from .project.project import Project
from .scripts import SCRIPTS
from .utils.animations import load_animation, splash_animation
from .ui.launchpad_ui import LaunchpadUI


def main() -> None:
    """Run the project"""

    parser = argparse.ArgumentParser("CC/v2", description="CoverCreator version 2")
    for n, _ in SCRIPTS:
        parser.add_argument(f"--{n}", nargs=argparse.REMAINDER)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--vpad", action="store_true")
    parser.add_argument("--audiodevice", type=str, required=False, default=None)
    parser.add_argument("file", nargs="?")

    args = parser.parse_args(sys.argv[1:])

    logger.init(args.verbose)

    for name, script in SCRIPTS:
        if script_args := getattr(args, name):
            sys.exit(script(script_args))

    logger.debug("Clearing cache directory")
    Project.clear()

    # Open and load things
    audio_route.mx_init(args.audiodevice)
    VersionLoader.register_all()
    Lightmap.load_all()
    Keyframes.load_internal()
    Launchpad.open_all()
    Launchpad.broadcast_clear()
    LaunchpadUI.statechange()

    # Load project
    if args.file:
        logger.info("Loading project %s", args.file)
        load_finish = load_animation()

        Project.load(args.file)
        Project.CURRENT_PROJECT.v.bake()

        load_finish.set()

    splash_finish = splash_animation()

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
