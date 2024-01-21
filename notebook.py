# %% Load and manipulate the raw dataframe
import geopandas
import pandas
from pyproj import Transformer
import re
import os
import requests

def download_file_if_not_exists(url, fname=None):
    if fname is None:
        fname = os.path.basename(url)
    if not os.path.isfile(fname):
        session = requests.Session()
        with session.get(url, stream=True) as stream:
            stream.raise_for_status()
            with open(fname, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=8192):
                    f.write(chunk)

def get_iso_centre(row, dim):
    if row['iso_type'] == 'from_centroid':
        return row[f'centre_{dim}']
    elif row['iso_type'] == 'from_nearest_node':
        return row[f'node_{dim}']
    elif row['iso_type'] == 'from_nearest_stop':
        return row[f'stop_{dim}']
    else:
        return row[f'centre_{dim}']

def get_difference(a, b):
    if a.geometry.isna().all() or b.geometry.isna().all():
        return a
    return a.overlay(b, how='difference')

def download_isochrone(hash, area):
    url = f'https://opendata.arcgis.com/api/v3/datasets/{hash}_0/downloads/data?format=fgdb&spatialRefId=4326&where=1%3D1'
    fname = f'UK Travel Area Isochrones (Nov-Dec 2022) by Public Transport and Walking for {area} - Generalised to 10m.gdb.zip'
    download_file_if_not_exists(url, fname)
    return fname

# %% Define isochrone downloads
isochrones = {
    'London West': {'id': 'bc8991d1c01a4ae4966d9d69498d79b0'},
    'North West North': {'id': 'cc40d63181bb4a40a74ae2fa4b4c34b3'},
    'South East': {'id': 'cb6b4456531f4bc8b967f6b0f7982b5a'},
    'London East': {'id': '38f450b4fc4c44ceaf9155b3c3d8174e'},
    'Northern Ireland': {'id': '7f1c281b2561483891cd797b0f6fd463'},
    'East of England': {'id': '5f47f967f2424a5d93e241a577e5d066'},
    'East Scotland': {'id': '2fbbd26d8c1443acaaba8260e975ca4d'},
    'South West': {'id': '5f2ba310492f47db962a60ac2ae6f29c'},
    'North East': {'id': '8b4ab8cce9a745efa781d7859912d6cc'},
    'West Midlands': {'id': '35112fe52bee479b8b948bcabb9dfcd3'},
    'North Scotland': {'id': 'e6b2cb05295042cfbf24dcddba2b97d2'},
    'East Midlands': {'id': 'f2a7af81406c4d93bb61de6be5481af4'},
    'North West South': {'id': 'ccf63c2fb6ec4eb789aeae13d0731134'},
    'Yorkshire and the Humber': {'id': '358fa09c34f14526be46cba124a96744'},
    'Wales': {'id': '17ea3de7defc4f72bdd95b998a5fe919'},
    'West Scotland North': {'id': 'b8626373ac284e24b9123fb8ecf55d01'},
    'West Scotland South': {'id': 'd1950a7db27d4b91b99748ad3924f472'},
}

# %% Get isochrones files
for area in isochrones.keys():
    print(f'Downloading file for {area}')
    # Get the data in EPSG:4326 so that we don't have to apply any conversion.
    # The geopandas CRS conversion from the website downloaded format of 27700 for NI is 
    # slightly offset, this avoids the offset
    isochrones[area]['fname'] = download_isochrone(isochrones[area]['id'], area)

# %% Process the files, making a geojson file for each isochrone starting point
for area in isochrones.keys():
    print(f'Processing data for {area}')
    if not os.path.exists(area):
        os.mkdir(area)
    if not os.path.isfile(isochrones[area]['fname']):
        raise Exception(f'Source file {isochrones[area]['fname']} missing')        
    # Load the file into a dataframe
    gdf = geopandas.read_file(isochrones[area]['fname'])
    # Convert the X/Y coordinates to the coordinate system we will use for mapping
    if area=='Northern Ireland':
        coordproj = "EPSG:29902"
    else:
        coordproj = "EPSG:27700"
    trans = Transformer.from_crs(coordproj, "EPSG:4326", always_xy=True)
    for pre in ['centre', 'node', 'stop']:
        gdf[f'{pre}_X'], gdf[f'{pre}_Y'] = trans.transform(gdf[f'{pre}_X'].values, gdf[f'{pre}_Y'].values)
    # Create new columns for the displayed isochrone centre point
    gdf['iso_centre_X'] = gdf.apply(get_iso_centre, axis=1, dim='X')
    gdf['iso_centre_Y'] = gdf.apply(get_iso_centre, axis=1, dim='Y')
    # Convert the travel time in seconds to minutes
    gdf['Travel Minutes'] = pandas.to_numeric(gdf['iso_cutoff'] / 60, downcast='integer')
    # Identify which area type is being used
    areatype = None
    for a in ['SA2011','OA21CD','OA11CD']:
        if a in gdf.columns:
            areatype = a
            break
    else:
        raise Exception(f'Unable to find expected area type in {area}')
    # Reduce down the size of the dataframe and then split by Small Area to minimise data accesses from the app
    reduced = gdf[[areatype,'iso_type','Travel Minutes','iso_centre_X','iso_centre_Y', 'geometry']]
    for sa in reduced[areatype].unique():
        original = reduced[reduced[areatype]==sa]
        min60 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 60, :], original.loc[lambda df: df['Travel Minutes'] == 45, :])
        min45 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 45, :], original.loc[lambda df: df['Travel Minutes'] == 30, :])
        min30 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 30, :], original.loc[lambda df: df['Travel Minutes'] == 15, :])
        min15 = original.loc[lambda df: df['Travel Minutes'] == 15, :]
        pandas.concat([min60, min45, min30, min15]).to_file(f'{area}/{sa}.geojson', driver='GeoJSON')

# %% Create a Small Area connectivity lookup for NI
gdf = geopandas.read_file(isochrones['Northern Ireland']['fname'])

# Load the Small Areas boundaries, preconverted to match geometries
sa2011 = geopandas.read_file('sa2011_epsg4326_simplified15.json')

# Find all SAs that are accessible from each SA
joined = gdf.sjoin(sa2011, how='inner', predicate='intersects',lsuffix='from',rsuffix='to')[['SA2011_from','SA2011_to','Travel Minutes']]

# Get the Small Area populations for 2020
pops = pandas.read_excel('SAPE20-SA-Totals.xlsx', sheet_name='Flat')
pops = pops[(pops['Area']=='Small Areas') & (pops['Year']==2020)][['Area_Code','MYE']]
joined = joined.merge(pops, how='inner', left_on='SA2011_from', right_on='Area_Code')
joined = joined.merge(pops, how='inner', left_on='SA2011_to', right_on='Area_Code', suffixes=['_from','_to'])
joined.to_csv('sa-connectivity.csv')

# %% Get Small Area statistics
# Load SA NI Multiple Index Of Deprivation data
nimdm = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='MDM')
nimdm.columns = nimdm.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()

# Load SA NI Multiple Index Of Deprivation income details
nimdm_income = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='Income')
nimdm_income.columns = nimdm_income.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()
nimdm = nimdm.merge(nimdm_income[['SA2011','Proportion of the population living in households whose equivalised income is below 60 per cent of the NI median']], how='left', left_on='SA2011', right_on='SA2011')

# Load SA NI Multiple Index Of Deprivation employment details
nimdm_employment = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='Employment')
nimdm_employment.columns = nimdm_employment.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()
nimdm = nimdm.merge(nimdm_employment[['SA2011','Proportion of the working age population who are employment deprived']], how='left', left_on='SA2011', right_on='SA2011')

# Load SA NI 2011 Census religion data
census = pandas.read_excel('census-2011-ks211ni.xlsx', sheet_name='SA', skiprows=5)
census.drop(columns=['SA','All usual residents'], inplace=True)
sa_stats = nimdm.merge(census, how='left', left_on='SA2011', right_on='SA Code')
sa_stats.to_csv('sa-stats.csv')

