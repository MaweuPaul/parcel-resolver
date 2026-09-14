import io
import zipfile

import shapefile

from parcel_resolver.conversion import parcels_to_shapefile_zip
from tests.fixtures.sample_parcels import SAMPLE_PARCELS


def test_shapefile_zip_contains_shp_shx_dbf():
    archive_bytes = parcels_to_shapefile_zip({"P001": SAMPLE_PARCELS["P001"]})

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())

    assert names == {"parcels.shp", "parcels.shx", "parcels.dbf"}


def test_shapefile_zip_includes_prj_when_crs_given():
    archive_bytes = parcels_to_shapefile_zip(
        {"P001": SAMPLE_PARCELS["P001"]},
        crs_wkt='GEOGCRS["WGS 84", ...]',
    )

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        assert "parcels.prj" in archive.namelist()


def test_shapefile_round_trips_parcel_geometry_and_id():
    archive_bytes = parcels_to_shapefile_zip({"P001": SAMPLE_PARCELS["P001"]})

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        shp = io.BytesIO(archive.read("parcels.shp"))
        shx = io.BytesIO(archive.read("parcels.shx"))
        dbf = io.BytesIO(archive.read("parcels.dbf"))

    reader = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)
    shapes = reader.shapes()
    records = reader.records()

    assert len(shapes) == 1
    assert records[0]["parcelid"] == "P001"
    # Every original corner shows up in the shapefile ring, regardless of
    # winding direction (the writer reorients outer rings clockwise).
    assert set(SAMPLE_PARCELS["P001"]) <= set(shapes[0].points)


def test_shapefile_writes_multiple_parcels():
    parcels = {
        "P001": SAMPLE_PARCELS["P001"],
        "P002": SAMPLE_PARCELS["P002"],
    }

    archive_bytes = parcels_to_shapefile_zip(parcels)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        shp = io.BytesIO(archive.read("parcels.shp"))
        shx = io.BytesIO(archive.read("parcels.shx"))
        dbf = io.BytesIO(archive.read("parcels.dbf"))

    reader = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)

    assert len(reader.shapes()) == 2
    assert {record["parcelid"] for record in reader.records()} == {"P001", "P002"}
