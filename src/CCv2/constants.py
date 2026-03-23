import os

import numpy as np


SRC = os.path.dirname(__file__)
ROOT = os.path.join(SRC, "..", "..")
LIGHTMAPS = os.path.join(ROOT, "lightmaps")
INTERNAL = os.path.join(ROOT, "internal")
INTERNAL_KEYFRAMES = os.path.join(INTERNAL, "keyframes")
INTERNAL_ICONS = os.path.join(INTERNAL, "icons")
CACHE = os.path.join(ROOT, "cache")
CACHE_KEYFRAMES = os.path.join(CACHE, "keyframes")
CACHE_AUDIO = os.path.join(CACHE, "audio")
CACHE_PAGES = os.path.join(CACHE, "pages")
STATIC_UI = os.path.join(ROOT, "web")

PROJ_EXT = ".lpz"
PDESC_EXT = ".lpj"
LIGHTMAP_EXT = ".lpm"
KEYFRAME_EXT = ".lpk"

SCHEMA_PROJECT_V1 = "../internal/schemas/project_v1.json"

AUDIO_TICKS = 20

SAMPLE_RATE = 44100
SAMPLE_DEPTH = np.int16
SAMPLE_DEPTH_PG = -16
OUT_CHANNELS = 5


WEBUI_PORT = 2048
