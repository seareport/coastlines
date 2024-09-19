from __future__ import annotations

import logging
import pathlib
import typing as T
import zipfile

import geopandas as gpd
import httpx

logger = logging.getLogger(__name__)


def download(provider: str, url: str, path: pathlib.Path) -> None:
    if path.exists() and path.stat().st_size:
        logger.info("%s: Archive already exists. Skipping download: %s", provider, path)
    else:
        logger.info("%s: Downloading %s to: %s", provider, url, path)
        with path.open("wb") as fd:
            with httpx.stream("GET", url) as r:
                for data in r.iter_bytes():
                    fd.write(data)


def extract_zip(provider, path):
    logger.info("%s: Extracting zip: %s", provider, path)
    with path.open("rb") as fd:
        zf = zipfile.ZipFile(fd)
        zf.extractall(path=path.parent)


def simplify_geometry(geo: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Make all geometries valid if necessary: https://stackoverflow.com/a/69283950
    if not geo.is_valid.all():
        geo = geo.make_valid().to_frame(name="geometry")
    assert geo.is_valid.all()
    # Merge what can be merged
    geo = gpd.GeoDataFrame(geometry=[geo.unary_union], crs=geo.crs)
    # Split the MultiGeometry to simple geometries
    # E.g. from one MultiPolygon -> multiple Polygons
    geo = T.cast(gpd.GeoDataFrame, geo.explode(ignore_index=True))
    assert geo.is_valid.all()
    return geo
