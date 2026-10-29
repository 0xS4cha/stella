# Stella

Astrophotography automation for the Nikon D60: camera control over USB, star-quality analysis of captured frames and observing-conditions data, as the foundation for learning optimal exposure settings.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- libgphoto2 (`brew install libgphoto2` on macOS)

On macOS the system `PTPCamera` daemon grabs the camera as soon as it is plugged in. Run `killall PTPCamera` before using Stella if the connection fails.

## Setup

```sh
uv sync
uv run stella --help
```

## Usage

### Camera

```sh
stella settings list [--json]
stella settings get iso
stella settings set iso=1600 shutterspeed=30
stella settings load settings.json
stella profile list
stella profile apply astro-d60 --override iso=800
stella capture --count 10 --interval 35 --output captures
```

Settings are validated against the choices reported by the camera and written in a single transaction. Each capture session creates a timestamped folder containing the downloaded files and a `manifest.jsonl` with the settings used for every shot.

The `astro-d60` profile requires the mode dial on **M** and assumes manual focus. Setting names and values differ between camera models: check them with `stella settings get <name>`.

### Image analysis

```sh
stella analyze captures/2026-10-29T22-00-00/*.NEF [--json] [--full-size]
```

RAW files are decoded linearly, then the background is modelled and stars are extracted. Every frame gets metrics (background level and noise, star count and density, FWHM, elongation, SNR, clipping) and a weighted quality score between 0 and 1.

### Observing conditions

```sh
export STELLA_LATITUDE=48.85 STELLA_LONGITUDE=2.35
stella env now --bortle 6 --focal-length 18 --aperture 3.5
stella env night --date 2026-10-29
```

This command combines sun and Moon positions (skyfield, the ephemeris is downloaded on first use), astronomical darkness windows, Open-Meteo forecasts (clouds, humidity, dew point, wind), sky quality (Bortle/SQM) and the maximum untrailed exposure (500 and NPF rules).

## Layout

```
src/stella/
  camera/        gphoto2 connection, typed settings, profiles, capture sessions
  analysis/      frame loading, background, star detection, metrics, scoring
  environment/   location, astronomy, weather, sky quality, optics, snapshots
  cli/           subcommands, one module per command
tests/           unit tests with a fake gphoto2 camera and synthetic star fields
```

## Development

```sh
uv run pytest
```
