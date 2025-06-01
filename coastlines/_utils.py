from __future__ import annotations

import json
import logging
import os
import pathlib
import typing as T
import zipfile

import geopandas as gpd
import httpx
import numpy as np
import numpy.typing as npt
import pyogrio
import pyproj
import shapely

logger = logging.getLogger(__name__)

NPArray: T.TypeAlias = npt.NDArray[np.float64]

STEREO = pyproj.CRS(("esri", 102018))
WGS84 = pyproj.CRS(("epsg", 4326))
WGS84_GEOD = pyproj.Geod(ellps="WGS84")
AREA = WORLD_SINUSOIDAL = pyproj.CRS(("esri", 54008))


def to_file(gdf: gpd.GeoDataFrame, filename: str | os.PathLike[str], **kwargs: T.Any):
    if gdf.attrs:
        kwargs.setdefault("layer_metadata", {})["PANDAS_ATTRS"] = json.dumps(gdf.attrs)
    gdf.to_file(filename, **kwargs)


def read_file(
    filename: str | os.PathLike[str],
    layer: str | None = None,
    **kwargs: T.Any,
) -> gpd.GeoDataFrame:
    info = pyogrio.read_info(filename, layer=layer, **kwargs)
    gdf = T.cast(gpd.GeoDataFrame, gpd.read_file(filename, engine="pyogrio", layer=layer, **kwargs))
    if layer_metadata := info["layer_metadata"]:
        if pandas_attrs := layer_metadata.get("PANDAS_ATTRS"):
            gdf.attrs.update(json.loads(pandas_attrs))
    return gdf


def download(provider: str, url: str, path: pathlib.Path) -> None:
    if path.exists() and path.stat().st_size:
        logger.info("%s: Archive already exists. Skipping download: %s", provider, path)
    else:
        logger.info("%s: Downloading %s to: %s", provider, url, path)
        with path.open("wb") as fd:
            with httpx.stream("GET", url) as r:
                for data in r.iter_bytes():
                    fd.write(data)


def extract_zip(provider: str, path: pathlib.Path) -> None:
    logger.info("%s: Extracting zip: %s", provider, path)
    with path.open("rb") as fd:
        zf = zipfile.ZipFile(fd)
        zf.extractall(path=path.parent)


def simplify_geometry(geo: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Make all geometries valid if necessary: https://stackoverflow.com/a/69283950
    if not np.all(geo.is_valid):
        geo = geo.make_valid().to_frame(name="geometry")
    assert np.all(geo.is_valid)
    # Merge what can be merged
    geo = gpd.GeoDataFrame(geometry=[geo.unary_union], crs=geo.crs)
    # Split the MultiGeometry to simple geometries
    # E.g. from one MultiPolygon -> multiple Polygons
    geo = T.cast(gpd.GeoDataFrame, geo.explode(ignore_index=True))
    assert np.all(geo.is_valid)
    return geo


def calc_area_and_perimeter(
    gdf: gpd.GeoDataFrame,
    geod: pyproj.Geod = WGS84_GEOD,
    *,
    sort: bool = False,
) -> gpd.GeoDataFrame:
    assert gdf.crs is not None, "CRS must be defined!"
    geometry_area_perimeter = np.vectorize(geod.geometry_area_perimeter)
    area, perimeter = geometry_area_perimeter(gdf.to_crs(WGS84).geometry.exterior)
    area *= -1
    gdf = gdf.assign(
        wgs84_area=area,
        wgs84_perimeter=perimeter,
        no_coords=gdf.count_coordinates() - 1,
    )
    if sort:
        gdf = gdf.sort_values("wgs84_area", ascending=False).reset_index(drop=True)
    return gdf
