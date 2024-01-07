# NI Travel app

A [searchable map of NI](https://pbarber.github.io/ni-travel-app) showing areas that can be reached from different locations using public transport within 15/30/45/60 minutes.

## Datasets

The app makes use of two open datasets:

* Isochrones: the boundaries of the areas that can be reached using public transport from each Small Area in NI
* Small Area Boundaries: the boundaries of Small Areas in NI

It also uses [OpenStreetMap](https://www.openstreetmap.org/)/[Nominatim](https://wiki.openstreetmap.org/wiki/Nominatim) to provide the search results.

### Isochrones

The data used in the app comes from [here](https://geoportal.statistics.gov.uk/datasets/7f1c281b2561483891cd797b0f6fd463/explore), and contains four entries for each Small Area (`SA2011`) in NI (4537 Small Areas), on date 2022-12-06. The four entries have `iso_cutoff` of 900, 1800, 2700 and 3600.

The original data source is [ArcGIS](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Northern_Ireland_Isochrones_Gen/FeatureServer). The best documentation I have found is [here](https://geoportal.statistics.gov.uk/datasets/ons::uk-travel-area-isochrones-nov-dec-2022-by-public-transport-and-walking-for-north-west-north-generalised-to-10m/about).

The meaning of `iso_cutoff` is:

> The maximum travel time, in seconds, to construct the reachable area/isochrone. Values are either 900, 1800, 2700, or 3600 which correspond to 15, 30, 45, and 60 minute limits respectively.

The centre point used is key to plotting on a map, this is defined by `iso_type`. Most values are `from_centroid` but other are used, so this needs to be dynamic. Though, given that the data is at Small Area level, probably just simplest to map Small Area initially.

Whilst the shapes of the areas are in WGS84, the centroid/stop/node coordinates are in Irish Grid.

I split the isochrones dataset into one file per Small Area, in order to save the app from having to download the whole dataset. This conversion process is handled in [notebook.py](notebook.py). The files are hosted on AWS S3.

### Small Area Boundaries

To understand the Small Areas, I used [the NISRA Small Area Boundaries dataset](https://admin.opendatani.gov.uk/dataset/nisra-open-data-boundaries-small-areas-2011). Note that to use a base map with the GeoJSON in [mapshaper](https://mapshaper.org), you need to run:

```
-proj from=EPSG:29902 crs=EPSG:4326
```

To use the Small Areas dataset in the app, I applied the conversion above in mapshaper, then simplified the file to 15% of the original.

## App

To run the app, open [index.html](index.html) in a web browser. The app consists of a single HTML file and uses JavaScript.

Key JavaScript libraries used are:

* [Leaflet](https://leafletjs.com/) - for the base map, markers, zoom
* [Deck.gl](https://deck.gl/) - for the coloured isochrone overlay
* [Deck.gl-Leaflet](https://github.com/zakjan/deck.gl-leaflet) - to combine the overlay and the map
* [Leaflet Control Geocoder](https://github.com/perliedman/leaflet-control-geocoder) - for the search box and results
* [Leaflet.PointInPolygon](https://github.com/hayeswise/Leaflet.PointInPolygon) - to find the searched point's isochrone

## Python setup

To create the map file, use the following.

Developed in Visual Studio Code using the [Remote-Containers](https://code.visualstudio.com/docs/devcontainers/containers) extension. To start the container, open `docker-compose.yml` and select `Docker: Compose Up`. Then find the `ni-travel-app_dev` container and right-click it, choose `Attach Visual Studio Code`. This will open a new window within the container. The first time you run the container you will need to install the Python extension, and choose the Python interpreter at `/usr/local/bin/python`.

To run the processing script run the following in the VS Code terminal:

```bash
python process.py --help
```

Key Python libraries used are:

* [Geopandas](https://geopandas.org/en/stable/) - for manipulating the isochrone dataset
* [Pandas](https://pandas.pydata.org/) - for general data manipulation
* [Requests](https://requests.readthedocs.io/en/latest/) - for getting data from URLs
