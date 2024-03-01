from __future__ import annotations

import pathlib

import geopandas as gpd
import pytest


GSHHG_RESOLUTIONS = 5
OSM_FILES = 10


def test_no_parquets():
    files = list(pathlib.Path("out").glob("*.parquet"))
    assert len(files) == GSHHG_RESOLUTIONS + OSM_FILES


@pytest.mark.parametrize("path", pathlib.Path("out").glob("*.parquet"))
def test_read_file(path):
    gdf = gpd.read_parquet(path)
    assert len(gdf) > 0
