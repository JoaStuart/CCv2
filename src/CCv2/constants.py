import os

from utils.runtime import RuntimeVars


SRC = os.path.dirname(__file__)
ROOT = os.path.join(SRC, "..", "..")
LIGHTMAPS = os.path.join(ROOT, "lightmaps")
INTERNAL = os.path.join(ROOT, "internal")
INTERNAL_KEYFRAMES = os.path.join(INTERNAL, "keyframes")
INTERNAL_ICONS = os.path.join(INTERNAL, "icons")
CACHE = os.path.join(ROOT, "cache")
CACHE_KEYFRAMES = os.path.join(CACHE, "keyframes")
CACHE_AUDIO = os.path.join(CACHE, "audio")

SAMPLE_RATE = 44100

RUNTIME = RuntimeVars()
