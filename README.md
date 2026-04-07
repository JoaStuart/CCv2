# CC/v2 (Launchpad Cover Creator)

## More readme coming soon

## Supported Launchpads

| Name               |     | NOVLPD                  |     | Support                                                                |
| ------------------ | --- | ----------------------- | --- | ---------------------------------------------------------------------- |
| Launchpad          |     | <small>NOVLPD01</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |
| Launchpad S        |     | <small>NOVLPD02</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |
| Launchpad Pro      |     | <small>NOVLPD03</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |
| Launchpad Mini Mk1 |     | <small>NOVLPD05</small> |     | ![Soon expected](https://img.shields.io/badge/Soon_expected-%23C87C09) |
| Launchpad Mini Mk2 |     | <small>NOVLPD08</small> |     | ![Not yet](https://img.shields.io/badge/Not_yet-%239D3107)             |
| Launchpad Mk2      |     | <small>NOVLPD09</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |
| Launchpad Mini Mk3 |     | <small>NOVLPD11</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |
| Launchpad X        |     | <small>NOVLPD12</small> |     | ![Not yet](https://img.shields.io/badge/Not_yet-%239D3107)             |
| Launchpad Pro Mk3  |     | <small>NOVLPD13</small> |     | ![Supported](https://img.shields.io/badge/Supported-%23409D07)         |

<sub>If you find a Launchpad that is not in this list, please open an issue :)</sub>

### Soon expected

Support will be added in a few weeks by me, it might take a little tho

### Not yet

Support might be added later, I still plan on collecting all Launchpads so basically also a matter of time but it might take a little longer

## Running from source

Building isn't quite finished yet, mostly after the major changes of static files in the recent UI update so running from source is the easier at the moment.

<small>

- Keep in mind, creating a `venv` is recommended!

- Python 3.14 and ffmpeg are required to run

</small>

### Download project and dependencies

```bash
git clone -r https://github.com/JoaStuart/CCv2.git
cd CCv2
pip install -e .
```

### Running

```bash
python -m CCv2
```
