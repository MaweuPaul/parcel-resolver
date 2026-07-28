from parcel_resolver.resolver.index import find_overlaps

def extract_coordinates(feature: dict) -> list[tuple[float, float]]:
    """
    Extracts coordinates from a GeoJSON object.

    Args:
        feature (dict): A GeoJSON feature object.
"""

    if "geometry" not in feature:
        raise ValueError("Invalid GeoJSON: Missing 'geometry' key")
    
    if feature["geometry"]["type"] != "Polygon":
        raise ValueError("Invalid GeoJSON: Only Polygon geometries are supported")
    
    if "coordinates" not in feature["geometry"]:
        raise ValueError("Invalid GeoJSON: Missing 'coordinates' key in geometry")
    
    return [tuple(coord) for coord in feature["geometry"]["coordinates"][0]]


def parse_feature_collection(feature_collection:dict) -> dict[str, list[tuple[float, float]]]:
    """
    Parses a GeoJSON FeatureCollection and extracts parcel coordinates.

    Args:
        feature_collection (dict): A GeoJSON FeatureCollection object."""
        
    parcels = {}
        
    for feature in feature_collection["features"]:
        parcel_id =feature["properties"]["parcelid"]
        coordinates = extract_coordinates(feature)
        parcels[parcel_id] = coordinates

    return parcels


# testing data

if __name__ == "__main__":
    sample_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"parcelid": "P001"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [0, 0],
                            [10, 0],
                            [10, 10],
                            [0, 10],
                            [0, 0],
                        ]
                    ],
                },
            },
            {
                            "type": "Feature",
                            "properties": {"parcelid": "P002"},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                         [10, 0],
    [20, 0],
    [20, 10],
    [10, 10],
    [10, 0],
                                    ]
                                ],
                            },
                }
        ],
    }

    parcels = parse_feature_collection(sample_collection)

    overlaps = find_overlaps(parcels)
    print("Overlaps:", overlaps)
    print(parcels)