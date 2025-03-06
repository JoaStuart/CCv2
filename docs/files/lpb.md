# Launchpad page buttons (LPB)

This file format holds timestamps for all buttons on a page and their respective timestamps.

## Format

### Version 1

```text
{
    TIMESTAMP       [ float32 timestamp for the following button to start at ]

    POSITION        [ uint8 packed position of the button ]
} [ repeated for all buttons on the current page ]
```
