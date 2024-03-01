from __future__ import annotations

import logging
import pathlib
import typing as T
import zipfile

import geopandas as gpd
import httpx
import multifutures

from coastlines import _utils

logger = logging.getLogger(__name__)


PROVIDER = "osm"
RAW_DIR = pathlib.Path("raw") / "osm"
OUT_DIR = pathlib.Path("out")
BASE_URL = "https://osmdata.openstreetmap.de/download/{filename}.zip"
FILES = {
    "osm_coastlines_split_3857": "coastlines-split-3857",
    "osm_coastlines_split_4326": "coastlines-split-4326",
    "osm_land_complete_3857": "land-polygons-complete-3857",
    "osm_land_complete_4326": "land-polygons-complete-4326",
    "osm_land_simplified_complete_3857": "simplified-land-polygons-complete-3857",
    "osm_land_split_3857": "land-polygons-split-3857",
    "osm_land_split_4326": "land-polygons-split-4326",
    "osm_water_simplified_split_3857": "simplified-water-polygons-split-3857",
    "osm_water_split_3857": "water-polygons-split-3857",
    "osm_water_split_4326": "water-polygons-split-4326",
}


RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def osm_read_shapefile(filename: str, **kwargs: T.Any) -> gpd.GeoDataFrame:
    path = next((RAW_DIR / filename).glob("*.shp"))
    logger.info("Parsing %s", path)
    gdf = T.cast(gpd.GeoDataFrame, gpd.read_file(path, engine="pyogrio", **kwargs))
    return gdf


def serialize(gdf: gpd.GeoDataFrame, output_name: str) -> None:
    path = OUT_DIR / f"{output_name}.parquet"
    logger.info("Parsing %s", path)
    gdf.to_parquet(path)


def multi_download(filenames: list[str]) -> None:
    logger.info("%s: Downloading archives", PROVIDER)
    paths = [RAW_DIR / f"{filename}.zip" for filename in filenames]
    urls = [BASE_URL.format(filename=filename) for filename in filenames]
    multifutures.multithread(
        func=_utils.download,
        func_kwargs=[
            {"provider": PROVIDER, "url": url, "path": path}
            for (url, path) in zip(urls, paths, strict=True)
        ],
        check=True,
    )


def multi_extract(filenames: list[str]) -> None:
    logger.info("%s: Extracting archives", PROVIDER)
    paths = [RAW_DIR / f"{filename}.zip" for filename in filenames]
    multifutures.multiprocess(
        func=_utils.extract_zip,
        func_kwargs=[{"provider": PROVIDER, "path": path} for path in paths],
        check=True,
    )


def main() -> None:
    filenames = list(FILES.values())
    multi_download(filenames)
    multi_extract(filenames)
