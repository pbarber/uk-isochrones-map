# %% Load and manipulate the raw dataframe
import geopandas
import pandas
from pyproj import Transformer
import re

def get_iso_centre(row, dim):
    if row['iso_type'] == 'from_centroid':
        return row[f'centre_{dim}']
    elif row['iso_type'] == 'from_nearest_node':
        return row[f'node_{dim}']
    elif row['iso_type'] == 'from_nearest_stop':
        return row[f'stop_{dim}']
    else:
        return row[f'centre_{dim}']

df = geopandas.read_file('UK_Travel_Area_Isochrones_(Nov_Dec_2022)_by_Public_Transport_and_Walking_for_Northern_Ireland_-_Generalised_to_10m.geojson')

trans = Transformer.from_crs(
    "EPSG:29902",
    "EPSG:4326",
    always_xy=True,
)
for pre in ['centre', 'node', 'stop']:
    df[f'{pre}_X'], df[f'{pre}_Y'] = trans.transform(df[f'{pre}_X'].values, df[f'{pre}_Y'].values)

df['Travel Minutes'] = pandas.to_numeric(df['iso_cutoff'] / 60, downcast='integer')

df['iso_centre_X'] = df.apply(get_iso_centre, axis=1, dim='X')
df['iso_centre_Y'] = df.apply(get_iso_centre, axis=1, dim='Y')

# %% Reduce down the size of the dataframe and then split by Small Area to minimise data accesses from the app
def get_difference(a, b):
    if a.geometry.isna().all() or b.geometry.isna().all():
        return a
    return a.overlay(b, how='difference')

reduced = df[['SA2011','iso_type','Travel Minutes','iso_centre_X','iso_centre_Y', 'geometry']]
for sa in reduced['SA2011'].unique():
    original = reduced[reduced['SA2011']==sa]
    min60 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 60, :], original.loc[lambda df: df['Travel Minutes'] == 45, :])
    min45 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 45, :], original.loc[lambda df: df['Travel Minutes'] == 30, :])
    min30 = get_difference(original.loc[lambda df: df['Travel Minutes'] == 30, :], original.loc[lambda df: df['Travel Minutes'] == 15, :])
    min15 = original.loc[lambda df: df['Travel Minutes'] == 15, :]
    pandas.concat([min60, min45, min30, min15]).to_file(f'{sa}.geojson', driver='GeoJSON')

# %%
# Load the Small Areas boundaries, preconverted to match geometries
sa2011 = geopandas.read_file('sa2011_epsg4326_simplified15.json')

# Find all SAs that are accessible from each SA
joined = df.sjoin(sa2011, how='inner', predicate='intersects',lsuffix='from',rsuffix='to')[['SA2011_from','SA2011_to','Travel Minutes']]

# %%
# Get the Small Area populations for 2020
pops = pandas.read_excel('SAPE20-SA-Totals.xlsx', sheet_name='Flat')
pops = pops[(pops['Area']=='Small Areas') & (pops['Year']==2020)][['Area_Code','MYE']]
joined = joined.merge(pops, how='inner', left_on='SA2011_from', right_on='Area_Code')
joined = joined.merge(pops, how='inner', left_on='SA2011_to', right_on='Area_Code', suffixes=['_from','_to'])

# %%
nimdm = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='MDM')
nimdm.columns = nimdm.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()
joined = joined.merge(nimdm, how='left', left_on='SA2011_from', right_on='SA2011').drop(columns=['SA2011'])

# %%
nimdm = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='Income')
nimdm.columns = nimdm.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()
joined = joined.merge(nimdm[['SA2011','Proportion of the population living in households whose equivalised income is below 60 per cent of the NI median']], how='left', left_on='SA2011_from', right_on='SA2011').drop(columns=['SA2011'])

# %%
nimdm = pandas.read_excel('NIMDM17_SA%20-%20for%20publication.xls', sheet_name='Employment')
nimdm.columns = nimdm.columns.str.replace(re.compile('\(.+'), '', regex=True).str.replace('\n','').str.strip()
joined = joined.merge(nimdm[['SA2011','Proportion of the working age population who are employment deprived']], how='left', left_on='SA2011_from', right_on='SA2011').drop(columns=['SA2011'])

# %%
