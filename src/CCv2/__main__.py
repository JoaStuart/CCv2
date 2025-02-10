import sys
from launchpad.base import Launchpad
import argparse

from lighting.keyframes import Keyframes
from lighting.lightmanager import LightManager
from lightmap import Lightmap
import logger
from scripts.lightmap import create_lightmap

if __name__ != "__main__":
    print("Try executing this file directly!")
    exit(1)

parser = argparse.ArgumentParser("CC/v2", description="CoverCreator version 2")
parser.add_argument("--lightmap", "-l", action="store_true")
parser.add_argument("--verbose", action="store_true")

args = parser.parse_args(sys.argv[1:])

logger.init(args.verbose)

if args.lightmap:
    create_lightmap()
    exit(0)


# Open and load thigns
Lightmap.load_all()
Launchpad.open_all()
Keyframes.load_internal()

input("")
LightManager().play("test").wait()

input("")

Launchpad.broadcast_clear()
