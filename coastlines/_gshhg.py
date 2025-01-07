from __future__ import annotations

import logging
import pathlib
import typing as T

import geopandas as gpd
import pandas as pd
from shapely import Polygon

from coastlines import _utils

logger = logging.getLogger(__name__)

__all__: list[str] = [
    "gshhg_create_global",
    "gshhg_read_shapefile",
    "open_gshhg",
]

CRUDE: T.Literal["crude"] = "crude"
LOW: T.Literal["low"] = "low"
INTERMEDIATE: T.Literal["intermediate"] = "intermediate"
HIGH: T.Literal["high"] = "high"
FULL: T.Literal["full"] = "full"

SHORT_TO_LONG_GSHHG_RESOLUTIONS = {
    "c": CRUDE,
    "l": LOW,
    "i": INTERMEDIATE,
    "h": HIGH,
    "f": FULL,
}

VERSION = "2.3.7"
URL = f"http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-{VERSION}.zip"
RAW_DIR = pathlib.Path("raw") / "gshhg"
OUT_DIR = pathlib.Path("out")

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# https://stackoverflow.com/a/72832981/592289
# Types
GSHHGResolution = T.Literal["c", "l", "i", "h", "f", "low", "crude", "intermediate", "high", "full"]
GSHHGShoreline = T.Literal[1, 2, 3, 4, 5, 6]
# CONSTANTS
GSHHG_RESOLUTIONS: list[GSHHGResolution] = [
    resolution for resolution in T.get_args(GSHHGResolution) if len(resolution) == 1
]
GSHHG_SHORELINES: list[GSHHGShoreline] = list(T.get_args(GSHHGShoreline))


def is_resolution_valid(resolution: str) -> T.TypeGuard[GSHHGResolution]:
    return resolution[0].lower() in GSHHG_RESOLUTIONS


def is_shoreline_valid(shoreline: int) -> T.TypeGuard[GSHHGShoreline]:
    return shoreline in GSHHG_SHORELINES


def get_path(
    resolution: GSHHGResolution,
    shoreline: GSHHGShoreline,
    base_path: pathlib.Path = OUT_DIR,
) -> pathlib.Path:
    short_resolution = resolution[0].lower()
    long_resolution = SHORT_TO_LONG_GSHHG_RESOLUTIONS[short_resolution]
    path = base_path / f"gshhg_{long_resolution}_l{shoreline}.parquet"
    return path


def gshhg_read_shapefile(
    resolution: GSHHGResolution,
    shoreline: GSHHGShoreline,
    **kwargs: T.Any,
) -> gpd.GeoDataFrame:
    """Read specific shapefiles based on the resolution and the shoreline level"""
    assert is_resolution_valid(resolution)
    assert is_shoreline_valid(shoreline)
    resolved_resolution = resolution[0].lower()
    path = RAW_DIR / f"GSHHS_shp/{resolved_resolution}/GSHHS_{resolved_resolution}_L{shoreline}.shp"
    gdf = T.cast(gpd.GeoDataFrame, gpd.read_file(path, engine="pyogrio", **kwargs))
    return gdf


def gshhg_create_global(
    resolution: GSHHGResolution,
    shoreline: GSHHGShoreline = 6,
) -> gpd.GeoDataFrame:
    assert is_resolution_valid(resolution)
    assert is_shoreline_valid(shoreline)
    assert shoreline in (5, 6)
    w1 = gshhg_read_shapefile(resolution, shoreline=1, columns=["geometry"])
    w5_or_6 = gshhg_read_shapefile(resolution, shoreline=shoreline, columns=["geometry"])
    if (resolution in ["full", "f"]) and (shoreline in [5]):
        # Fix for Western Antarctic
        coords = list(w5_or_6.iloc[1].geometry.exterior.coords)
        coords[0] = [0, coords[0][1]]
        coords[1] = [0, coords[1][1]]
        w5_or_6.at[1, "geometry"] = Polygon(coords)
        # Fix for Eastern Antarctic
        coords = list(w5_or_6.iloc[0].geometry.exterior.coords)[1:-1]
        coords[0] = [180, coords[0][1]]
        w5_or_6.at[0, "geometry"] = Polygon(*coords, [[180.0, -90]])
    ws = _utils.simplify_geometry(T.cast(gpd.GeoDataFrame, pd.concat((w1, w5_or_6))))
    ws["area_m2"] = T.cast(gpd.GeoDataFrame, ws.to_crs(epsg=4087)).area
    ws = T.cast(gpd.GeoDataFrame, ws.sort_values(by="area_m2", ascending=False).reset_index(drop=True))
    ws = T.cast(gpd.GeoDataFrame, ws.drop(columns="area_m2"))
    return ws


def open_gshhg(
    resolution: GSHHGResolution,
    shoreline: GSHHGShoreline = 6,
    source_path: pathlib.Path = OUT_DIR,
    **kwargs: T.Any,
) -> gpd.GeoDataFrame:
    """Return a `GeoDataFrame` with the GSHHG coastlines at the specified `resolution`."""
    assert is_resolution_valid(resolution)
    assert is_shoreline_valid(shoreline)
    path = get_path(base_path=source_path, resolution=resolution, shoreline=shoreline)
    coastlines = gpd.read_parquet(path, **kwargs)
    return coastlines


def main(target_path: pathlib.Path) -> None:
    provider = "gshhg"
    zip_path = RAW_DIR / URL.rsplit("/", 1)[-1]
    _utils.download(provider=provider, url=URL, path=zip_path)
    _utils.extract_zip(provider=provider, path=zip_path)
    for resolution in GSHHG_RESOLUTIONS:
        for shoreline in GSHHG_SHORELINES[-2:]:
            output = get_path(base_path=target_path, resolution=resolution, shoreline=shoreline)
            logger.info(
                "%s: Creating global coastlines for %s resolution - shoreline level %s: %s",
                provider,
                SHORT_TO_LONG_GSHHG_RESOLUTIONS[resolution],
                shoreline,
                output,
            )
            w = gshhg_create_global(resolution, shoreline)
            w.to_file(str(output).replace("parquet", "gpkg"))
            # w.to_parquet(
            #    output,
            #    write_covering_bbox=True,
            #    schema_version="1.0.0",
            #    compression="zstd",
            #    engine="pyarrow",
            # )
    logger.info("%s: Done", provider)
