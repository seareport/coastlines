from __future__ import annotations

import logging
import pathlib
import typing as T
import zipfile

import geopandas as gpd
import httpx
import multifutures
import osmium
import osmium.filter
import pandas as pd
import pyogrio
import shapely

from coastlines import _utils

logger = logging.getLogger(__name__)


PROVIDER = "osm"
RAW_DIR = pathlib.Path("raw") / "osm"
OUT_DIR = pathlib.Path("out")
BASE_URL = "https://osmdata.openstreetmap.de/download/{filename}.zip"

NAMES = {
    # "coastlines-split-3857": "osm_coastlines_split_3857",
    # "coastlines-split-4326": "osm_coastlines_split_4326",
    # "land-polygons-complete-3857": "osm_land_complete_3857",
    "land-polygons-complete-4326": "osm_land_complete_4326",
    # "simplified-land-polygons-complete-3857": "osm_land_simplified_complete_3857",
    # "land-polygons-split-3857": "osm_land_split_3857",
    # "land-polygons-split-4326": "osm_land_split_4326",
    # "simplified-water-polygons-split-3857": "osm_water_simplified_split_3857",
    # "water-polygons-split-3857": "osm_water_split_3857",
    # "water-polygons-split-4326": "osm_water_split_4326",
}


RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def download_land_complete() -> None:
    _utils.download(
        provider=PROVIDER,
        url="https://osmdata.openstreetmap.de/download/osm_land_complete_4326.zip",
        path=RAW_DIR / "land-polygons-complete-4326.zip",
    )


def download_antarctica_pbf() -> None:
    _utils.download(
        provider=PROVIDER,
        url="https://download.geofabrik.de/antarctica-latest.osm.pbf",
        path=RAW_DIR / "antarctica-latest.osm.pbf",
    )


def extract_ice_shelves() -> gpd.GeoDataFrame:
    pbf = RAW_DIR / "antarctica-latest.osm.pbf"
    fp = osmium.FileProcessor(pbf)
    fp = fp.with_areas()
    fp = fp.with_locations()
    fp = fp.with_filter(osmium.filter.TagFilter(("glacier:type", "shelf")))
    # fp = fp.with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
    fp = fp.with_filter(osmium.filter.GeoInterfaceFilter())
    gdf = gpd.GeoDataFrame.from_features(fp)
    gdf = gpd.GeoDataFrame(geometry=shapely.get_parts(gdf.union_all()), crs=4326)
    return gdf



def main(target_path: pathlib.Path) -> None:
    download_land_complete()
    download_antarctica_pbf()
    path = f"/vsizip/{RAW_DIR}/land-polygons-complete-4326.zip/land-polygons-complete-4326/land_polygons.shp"
    osm = _utils.read_file(path)
    ice_shelves = extract_ice_shelves()
    antarctica = osm.clip((-180, -90, 180, -60))
    rest_of_world = osm.clip((-180, -60, 180, 90))
    antarctica_grounding = gpd.overlay(antarctica, ice_shelves, how='difference') \
        .explode().normalize().to_frame("geometry")
    osm_grounding = pd.concat([rest_of_world[["geometry"]], antarctica_grounding], ignore_index=True) \
        .normalize().to_frame("geometry")
    osm_grounding.attrs.update(osm.attrs)
    _utils.to_file(
        gdf=_utils.calc_area_and_perimeter(osm),
        filename=OUT_DIR / "osm_land_complete_4326.gpkg",
    )
    _utils.to_file(
        gdf=_utils.calc_area_and_perimeter(osm_grounding),
        filename=OUT_DIR / "osm_land_complete_grounding_4326.gpkg",
    )
