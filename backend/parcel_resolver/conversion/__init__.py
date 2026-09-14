import io
import zipfile

import shapefile
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient


def parcels_to_shapefile_zip(
    parcels: dict[str, list[tuple[float, float]]],
    crs_wkt: str | None = None,
) -> bytes:
    """
    Packages parcel polygons into a zipped ESRI Shapefile.

    Args:
        parcels: A {parcel_id: [(x, y), ...]} dictionary, the same shape
            every other tool in this codebase uses.
        crs_wkt: An optional WKT coordinate reference system string. When
            given, a .prj file is included in the archive so GIS software
            that reads it knows what the coordinates mean.

    Returns:
        The raw bytes of a .zip archive containing parcels.shp, parcels.shx,
        parcels.dbf, and (if crs_wkt was given) parcels.prj.
    """
    shp_buffer = io.BytesIO()
    shx_buffer = io.BytesIO()
    dbf_buffer = io.BytesIO()

    writer = shapefile.Writer(
        shp=shp_buffer, shx=shx_buffer, dbf=dbf_buffer, shapeType=shapefile.POLYGON
    )
    writer.field("parcelid", "C", size=64)

    for parcel_id, coords in parcels.items():
        ring = list(coords)
        if ring[0] != ring[-1]:
            ring.append(ring[0])

        # The Shapefile spec requires outer rings to be wound clockwise;
        # this codebase's own parcel fixtures are wound counter-clockwise,
        # and GIS software that honors winding (ArcGIS in particular) reads
        # a counter-clockwise "outer" ring as a hole instead.
        ring = list(orient(Polygon(ring), sign=-1.0).exterior.coords)

        writer.poly([ring])
        writer.record(parcelid=parcel_id)

    writer.close()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("parcels.shp", shp_buffer.getvalue())
        archive.writestr("parcels.shx", shx_buffer.getvalue())
        archive.writestr("parcels.dbf", dbf_buffer.getvalue())
        if crs_wkt:
            archive.writestr("parcels.prj", crs_wkt)

    return zip_buffer.getvalue()
