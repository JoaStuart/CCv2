# Launchpad Keyframes (LPK)

This file format holds keyframe data that is used for displaying a lightshow animation on the launchpad.

## Format

### Version 1

```text
MAGIC_HEADER    [ [0xCC 0x01] stored as raw data - used to identify this file version ]

ANIM_TIME       [ float32 denoting the default animation duration ]
NUM_FRAMES      [ uint32 denoting the amount of frames stored ]

{

    POSITION    [ uint8 containing packed position (see below) ]

    RED         [ uint8 containing the red color channel for this button ]
    GREEN       [ uint8 containing the green color channel for this button ]
    BLUE        [ uint8 containing the blue color channel for this button ]

} [ repeated for each frame ]
```

#### Unpacking packed position

```text
X = (POS >> 4) - 1
Y = (POS & 0xF) - 1
```

#### Packing positions

```text
POS = ((X + 1) << 4) | (Y + 1)
```
