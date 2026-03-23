import threading

from ..lighting.keyframes import Keyframes
from ..lighting.lightmanager import KfData, LightManager


def _play(anim: str) -> threading.Event:
    """Play keyframes in the background and return an event
    that gets triggered when finished playback

    Args:
        anim (str): The name of the animation

    Returns:
        threading.Event: The event indicating the end of playback
    """

    return LightManager().play(anim)


def _persistent(anim: str) -> threading.Event:
    """Play a keyframe repeatedly until the returned event is set

    Args:
        anim (str): The animation to play

    Returns:
        threading.Event: The event to end the playback
    """

    load_finish = threading.Event()
    LightManager().play_raw(KfData(Keyframes.FRAME_CACHE[anim].persistent(load_finish)))
    return load_finish


def load_animation() -> threading.Event:
    """Play the loading animation with entry

    Returns:
        threading.Event: The event to stop the animation
    """

    _play("__loading_entry").wait()

    return _persistent("__loading")


def splash_animation() -> threading.Event:
    """Play the splash animation with entry

    Returns:
        threading.Event: The event to stop the animation
    """

    _play("__splash_entry").wait()

    return _persistent("__splash")
