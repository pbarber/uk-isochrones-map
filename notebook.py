# %% Load and manipulate the raw dataframe
import geopandas
import pandas
from pyproj import Transformer

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

# %%
df.head()

# %% Reduce down the size of the dataframe and then split by Small Area to minimise data accesses from the app
reduced = df[['SA2011','iso_type','Travel Minutes','iso_centre_X','iso_centre_Y', 'geometry']]
for sa in reduced['SA2011'].unique():
    original = reduced[reduced['SA2011']==sa]
    min60 = original.loc[lambda df: df['Travel Minutes'] == 60, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 45, :], how='difference')
    min45 = original.loc[lambda df: df['Travel Minutes'] == 45, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 30, :], how='difference')
    min30 = original.loc[lambda df: df['Travel Minutes'] == 30, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 15, :], how='difference')
    min15 = original.loc[lambda df: df['Travel Minutes'] == 15, :]
    pandas.concat([min60, min45, min30, min15]).to_file(f'{sa}.geojson', driver='GeoJSON')

# %%
df.groupby('iso_type').count()

# %%
original = reduced[reduced['SA2011']=='N00000897']
min60 = original.loc[lambda df: df['Travel Minutes'] == 60, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 45, :], how='difference')
min45 = original.loc[lambda df: df['Travel Minutes'] == 45, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 30, :], how='difference')
min30 = original.loc[lambda df: df['Travel Minutes'] == 30, :].overlay(original.loc[lambda df: df['Travel Minutes'] == 15, :], how='difference')
min15 = original.loc[lambda df: df['Travel Minutes'] == 15, :]
pandas.concat([min60, min45, min30, min15]).to_file('N00000897.geojson', driver='GeoJSON')



# %%
