# Launchpad Project File (LPZ)

This file format holds the entire cover project in a ZIP format. Alas, this file is just a normal ZIP file with DEFLATE compression, but has a set structure to the internal files

## Structure

### Version 1

```text
FILE.lpz
├─── project.lpj [ see lpj file docs ]
│
├─── audio
│    └─── [ all audio files to load for the project - all types `librosa` supports ]
│
├─── buttons
│    └─── [0-8].lpb [ one file each page - see lpb file docs ]
│
└─── keyframes
     └─── [ all keyframes used inside the project - see lpk file docs ]

```

- [LPJ file documentation](lpj.md)
- [LPB file documentation](lpb.md)
- [LPK file documentation](lpk.md)
