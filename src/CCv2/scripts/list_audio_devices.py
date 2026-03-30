import pygame.mixer as mx
import pygame._sdl2.audio as sdlaud


def list_audio_devices():
    mx.init()

    print("Detected audio devices:")
    for o in sdlaud.get_audio_device_names(iscapture=False):
        print("  -", o)
