import os
import zipfile

import xarray as xr

nc_file = "data/raw/era5_raw.nc"

if zipfile.is_zipfile(nc_file):
    print("Extracting ZIP...")
    with zipfile.ZipFile(nc_file, "r") as zip_ref:
        zip_ref.extractall(os.path.dirname(nc_file))
        extracted = [f for f in zip_ref.namelist() if f.endswith((".nc", ".grib", ".grib2"))]
        if extracted:
            nc_file = os.path.join(os.path.dirname(nc_file), extracted[0])
            print(f"Using file: {nc_file}")

ds = xr.open_dataset(nc_file, engine="netcdf4")
print(f"\nDimensions: {list(ds.dims)}")
print(f"Coordinates: {list(ds.coords)}")
print(f"Variables: {list(ds.data_vars)}")
print(f"\nDataset structure:")
print(ds)
