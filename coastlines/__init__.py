from __future__ import annotations

import importlib.metadata

from coastlines._gshhg import gshhg_create_global
from coastlines._gshhg import gshhg_read_shapefile
from coastlines._gshhg import open_gshhg
from coastlines._osm import osm_read_shapefile
from coastlines._utils import simplify_geometry


__version__ = importlib.metadata.version(__name__)


__all__ = [
    "__version__",
    "gshhg_create_global",
    "gshhg_read_shapefile",
    "open_gshhg",
    "osm_read_shapefile",
    "simplify_geometry",
]
