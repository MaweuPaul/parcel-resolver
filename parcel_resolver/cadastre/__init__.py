from shapely.geometry import Polygon 


# valideates teh parcel
def validate_parcel (coords :list[tuple[float, float]]) -> dict:

    # flags for all suspicition polygons
    flags =[]
    polygon = Polygon(coords)
    is_valid =polygon.is_valid


    area =polygon.area

    if not is_valid:
            flags.append("self intersecting")

    if area < 1 or area > 1000000:
        flags.append("suspicious area")
    return {
        "is_valid": is_valid,
        "area": area,
        "flags": flags
    }



