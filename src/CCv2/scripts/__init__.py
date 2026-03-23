from .saveconvert import convert_savefile
from .lightmap import create_lightmap

SCRIPTS = [
    ("saveconvert", convert_savefile),
    ("lightmap", create_lightmap),
]
