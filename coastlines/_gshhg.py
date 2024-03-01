from __future__ import annotations

import logging
import pathlib
import typing as T

import geopandas as gpd
import pandas as pd

from coastlines import _utils

logger = logging.getLogger(__name__)

__all__: list[str] = [
    "gshhg_create_global",
    "gshhg_read_shapefile",
    "gshhg_read_global",
]

VERSION = "2.3.7"
URL = f"http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-{VERSION}.zip"
RAW_DIR = pathlib.Path("raw") / "gshhg"
OUT_DIR = pathlib.Path("out")

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# https://stackoverflow.com/a/72832981/592289
# Types
GSHHGResolution = T.Literal["f", "h", "i", "l", "c", "full", "high", "intermediate", "low", "crude"]
GSHHGShoreline = T.Literal[1, 2, 3, 4, 5, 6]
# CONSTANTS
GSHHG_RESOLUTIONS: set[GSHHGResolution] = set(T.get_args(GSHHGResolution))
GSHHG_SHORELINES: set[GSHHGShoreline] = set(T.get_args(GSHHGShoreline))


def is_resolution_valid(resolution: str) -> T.TypeGuard[GSHHGResolution]:
    return resolution in GSHHG_RESOLUTIONS


def is_shoreline_valid(shoreline: int) -> T.TypeGuard[GSHHGShoreline]:
    return shoreline in GSHHG_SHORELINES


def gshhg_read_shapefile(
    resolution: GSHHGResolution,
    shoreline: GSHHGShoreline,
    **kwargs: T.Any,
) -> gpd.GeoDataFrame:
    """Read specific shapefiles based on the resolution and the shoreline level"""
    assert is_resolution_valid(resolution)
    assert is_shoreline_valid(shoreline)
    path = RAW_DIR / f"GSHHS_shp/{resolution}/GSHHS_{resolution.lower()}_L{shoreline}.shp"
    gdf = T.cast(gpd.GeoDataFrame, gpd.read_file(path, engine="pyogrio", **kwargs))
    return gdf


def gshhg_create_global(
    resolution: GSHHGResolution,
    antarctica_level: GSHHGShoreline = 6,
) -> gpd.GeoDataFrame:
    assert is_resolution_valid(resolution)
    assert is_shoreline_valid(antarctica_level)
    assert antarctica_level in (5, 6)
    w1 = gshhg_read_shapefile(resolution, shoreline=1, columns=["geometry"])
    w6 = gshhg_read_shapefile(resolution, shoreline=antarctica_level, columns=["geometry"])
    ws = _utils.simplify_geometry(T.cast(gpd.GeoDataFrame, pd.concat((w1, w6))))
    ws["area_m2"] = T.cast(gpd.GeoDataFrame, ws.to_crs(epsg=4087)).area
    ws = T.cast(gpd.GeoDataFrame, ws.sort_values(by="area_m2", ascending=False).reset_index(drop=True))
    ws = T.cast(gpd.GeoDataFrame, ws.drop(columns="area_m2"))
    return ws


def gshhg_read_global(resolution: GSHHGResolution, **kwargs: T.Any) -> gpd.GeoDataFrame:
    assert is_resolution_valid(resolution)
    coastlines = gpd.read_parquet(OUT_DIR / f"gshhg_{resolution}.parquet", **kwargs)
    return coastlines


def main() -> None:
    provider = "gshhg"
    zip_path = RAW_DIR / URL.rsplit("/", 1)[-1]
    _utils.download(provider=provider, url=URL, path=zip_path)
    _utils.extract_zip(provider=provider, path=zip_path)
    for resolution in ("c", "l", "i", "h", "f"):
        assert is_resolution_valid(resolution)
        output = OUT_DIR / f"gshhg_{resolution}.parquet"
        logger.info("%s: Creating global coastlines for %s resolution: %s", provider, resolution, output)
        w = gshhg_create_global(resolution)
        w.to_parquet(output)
    logger.info("%s: Done", provider)


if __name__ == "__main__":
    main()
