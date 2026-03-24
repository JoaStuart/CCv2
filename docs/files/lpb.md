# Launchpad page buttons (LPB)

This file format holds timestamps for all buttons on a page and their respective timestamps.

## Format

### Version 1

```text
{
    MAGIC_HEADER        [ [0x12 0x11] stored as raw data - used to identify this file ]
    {
        TIMESTAMP       [ float32 timestamp for the following button to start at ]

        POSITION X        [ int8 x position of the button ]
        POSITION Y        [ int8 y position of the button ]
    } [ repeated for all buttons on the current page ]
}
```
