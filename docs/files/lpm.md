# Launchpad Color Mappings

This file format hold mappings from velocity used by the launchpad to the color it displays.

## Format

### Version 1

```text
MAGIC_HEADER        [ [ 0x55 0x01 ] stored as raw data - used to identify this file version ]

{
    VELOCITY        [ uint8 denoting the velocity of the following color ]

    RED             [ uint8 containing the red color channel for this velocity ]
    GREEN           [ uint8 containing the green color channel for this velocity ]
    BLUE            [ uint8 containing the blue color channel for this velocity ]
} [ repeated for all velocities stored in this file ]
```
