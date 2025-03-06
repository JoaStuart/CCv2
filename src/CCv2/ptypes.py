import numpy as np


type int2 = tuple[int, int]
type int3 = tuple[int, int, int]
type int4 = tuple[int, int, int, int]


type AudioRaw = np.ndarray[tuple[int, int], np.dtype[np.int16]]

__all__ = ["int2", "int3", "int4", "AudioRaw"]
