from __future__ import annotations

import logging

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

app = cyclopts.App()
app["--help"].group = "Meta"
app["--version"].group = "Meta"


@app.command
def gshhg():
    """Download and extract data from GSHHG."""
    _gshhg.main()


@app.command
def naturalearth():
    """Download and extract data from Naturalearth."""
    _naturalearth.main()


@app.command
def osm():
    """Download and extract data from OpenStreetMaps."""
    _osm.main()


def main():
    app()


if __name__ == "__main__":
    main()
