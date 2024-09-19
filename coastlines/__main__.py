from __future__ import annotations

import logging
import pathlib

import cyclopts

from coastlines import _gshhg
from coastlines import _naturalearth
from coastlines import _osm


logging.basicConfig(
    level=20,
    style="{",
    format="{levelname:8s}; {asctime:s}; {name:<20s} {funcName:<35s} {lineno:4d}; {message:s}",
)
logger = logging.getLogger(__name__)


def _create_meta_group(app: cyclopts.App):
    app["--help"].group = "Meta"
    app["--version"].group = "Meta"


app = cyclopts.App(name="coastlines", help="Handle coastline data from various providers")

# Create subcommands
gshhg_app = cyclopts.App(name="gshhg", help="Handle GSHHG data")
naturalearth_app = cyclopts.App(name="naturalearth", help="Handle NaturalEarth data")
osm_app = cyclopts.App(name="osm", help="Handle OpenStreetMaps data")

# Register sub-commands
# app.command(gshhg_app)
# app.command(naturalearth_app)
# app.command(osm_app)

# Meta commands
_create_meta_group(app)
_create_meta_group(gshhg_app)
_create_meta_group(naturalearth_app)
_create_meta_group(osm_app)


@app.command(name="gshhg")
def gshhg_download_(
    target_path: pathlib.Path = pathlib.Path("out"),
) -> None:
    """Download and extract data from GSHHG."""
    target_path.mkdir(parents=True, exist_ok=True)
    _gshhg.main(target_path)


@app.command(name="naturalearth")
def naturalearth_download():
    """Download and extract data from Naturalearth."""
    _naturalearth.main()


@app.command(name="osm")
def osm_download():
    """Download and extract data from OpenStreetMaps."""
    _osm.main()


def main():
    app()


if __name__ == "__main__":
    main()
