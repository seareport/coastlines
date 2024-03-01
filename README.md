## `coastlines`

``` bash
git clone https://github.com/seareport/coastlines
cd coastlines
python3 -mvenv .venv
source .venv/bin/activate
poetry install
```

This will give install the `coastlines` CLI application.

## GSHHG

Download and process the GSHHG coastlines (fix polygon validity etc):
```
coastlines gshhg
```

## OpenStreetMaps

Download the OpenStreetMaps coastlines

``` bash
coastlines osm
```

## NaturalEarth

WIP
