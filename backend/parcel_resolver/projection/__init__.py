from pyproj import Transformer


def reproject_coordinates(
    coords: list[tuple[float, float]],
    source_crs: str,
    target_crs: str,
) -> list[tuple[float, float]]:
    """
    Reprojects a parcel's coordinates from one coordinate reference system
    to another.

    Args:
        coords: The parcel's (x, y) coordinates, in source_crs.
        source_crs: The CRS the input coordinates are already in, e.g.
            "EPSG:4326" for WGS84 latitude/longitude.
        target_crs: The CRS to reproject into, e.g. "EPSG:3857" for Web
            Mercator.

    Returns:
        The same coordinates, reprojected into target_crs.
    """
    # always_xy pins coordinate order to (x, y) / (lon, lat) regardless of
    # a CRS's own native axis order -- EPSG:4326 is defined as (lat, lon),
    # and without this every WGS84 input would come out transposed.
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return [transformer.transform(x, y) for x, y in coords]
