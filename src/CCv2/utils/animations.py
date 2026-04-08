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

import threading
from typing import Optional

from ..lighting.keyframes import Keyframes
from ..lighting.lightmanager import KfData, LightManager


def play(anim: str) -> threading.Event:
    """Play keyframes in the background and return an event
    that gets triggered when finished playback

    Args:
        anim (str): The name of the animation

    Returns:
        threading.Event: The event indicating the end of playback
    """

    return LightManager().play(anim)


def persistent(anim: str, event: Optional[threading.Event] = None) -> threading.Event:
    """Play a keyframe repeatedly until the returned event is set

    Args:
        anim (str): The animation to play

    Returns:
        threading.Event: The event to end the playback
    """

    load_finish = threading.Event() if event is None else event
    LightManager().play_raw(KfData(Keyframes.FRAME_CACHE[anim].persistent(load_finish)))
    return load_finish


def load_animation() -> threading.Event:
    """Play the loading animation with entry

    Returns:
        threading.Event: The event to stop the animation
    """

    play("__loading_entry").wait()

    return persistent("__loading")


def splash_animation() -> threading.Event:
    """Play the splash animation with entry

    Returns:
        threading.Event: The event to stop the animation
    """

    play("__splash_entry").wait()

    return persistent("__splash")
