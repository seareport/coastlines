from __future__ import annotations

import logging
import pathlib
import typing as T

from ._utils import download
from ._utils import extract_zip

logger = logging.getLogger(__name__)


RAW_DIR = pathlib.Path("raw") / "naturalearth"
OUT_DIR = pathlib.Path("out")
URL = "https://naciscdn.org/naturalearth/packages/natural_earth_vector.zip"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main(target_path: pathlib.Path) -> None:
    (target_path / "out").exists()

    # download(url=url, path=path)
    # extract_zip(path)
