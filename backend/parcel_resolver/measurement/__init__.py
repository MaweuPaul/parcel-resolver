from shapely.geometry import Polygon


def measure_parcel(coords: list[tuple[float, float]]) -> dict:
    """
    Measures a parcel's area and boundary length.

    Args:
        coords (list[tuple[float, float]]): Coordinates of the parcel.

    Returns:
        dict: The parcel's area and perimeter, in the square/linear units
        of the input coordinate system.
    """
    polygon = Polygon(coords)

    return {
        "area": polygon.area,
        "perimeter": polygon.length,
    }
