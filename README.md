# NI Travel app

Provides an interactive map of NI showing travel isochrones.

## App

How to run the app.

## Python setup

To play with the map file, use the following.

Developed in Visual Studio Code using the [Remote-Containers](https://code.visualstudio.com/docs/devcontainers/containers) extension. To start the container, open `docker-compose.yml` and select `Docker: Compose Up`. Then find the `ni-travel-app_dev` container and right-click it, choose `Attach Visual Studio Code`. This will open a new window within the container. The first time you run the container you will need to install the Python extension, and choose the Python interpreter at `/usr/local/bin/python`.

To run the processing script run the following in the VS Code terminal:

```bash
python process.py --help
```

## Datasets

### Isochrones

The data used in the app comes from [here](https://geoportal.statistics.gov.uk/datasets/7f1c281b2561483891cd797b0f6fd463/explore), and contains four entries for each Small Area (`SA2011`) in NI (4537 Small Areas), on date 2022-12-06. The four entries have `iso_cutoff` of 900, 1800, 2700 and 3600.

The original data source is [ArcGIS](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Northern_Ireland_Isochrones_Gen/FeatureServer). The best documentation I have found is [here](https://geoportal.statistics.gov.uk/datasets/ons::uk-travel-area-isochrones-nov-dec-2022-by-public-transport-and-walking-for-north-west-north-generalised-to-10m/about).

The meaning of `iso_cutoff` is:

> The maximum travel time, in seconds, to construct the reachable area/isochrone. Values are either 900, 1800, 2700, or 3600 which correspond to 15, 30, 45, and 60 minute limits respectively.

The centre point used is key to plotting on a map, this is defined by `iso_type`. Most values are `from_centroid` but other are used, so this needs to be dynamic. Though, given that the data is at Small Area level, probably just simplest to map Small Area initially.

Whilst the shapes of the areas are in WGS84, the centroid/stop/node coordinates are in Irish Grid.

### Small Area Boundaries

To understand the Small Areas, I used [the NISRA Small Area Boundaries dataset](https://admin.opendatani.gov.uk/dataset/nisra-open-data-boundaries-small-areas-2011). Note that to use a base map with the GeoJSON in mapshaper, you need to run:

```
-proj from=EPSG:29902 crs=EPSG:4326
```

I used N00000897 as my test Small Area.


