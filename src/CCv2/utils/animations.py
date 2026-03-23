import threading

from ..lighting.keyframes import Keyframes
from ..lighting.lightmanager import LightManager


def _play(anim: str) -> threading.Event:
    return LightManager().play_raw(Keyframes.FRAME_CACHE[anim])


def _persistent(anim: str) -> threading.Event:
    load_finish = threading.Event()
    LightManager().play_raw(Keyframes.FRAME_CACHE[anim].persistent(load_finish))
    return load_finish


def load_animation() -> threading.Event:
    _play("__loading_entry").wait()

    return _persistent("__loading")


def splash_animation() -> threading.Event:
    _play("__splash_entry").wait()

    return _persistent("__splash")
