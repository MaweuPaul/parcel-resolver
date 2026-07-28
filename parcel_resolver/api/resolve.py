from fastapi import FastAPI, HTTPException

from parcel_resolver.io.geojson import parse_feature_collection
from parcel_resolver.resolver.index import find_overlaps

app = FastAPI()

@app.post("/resolve")
async def resolve_parcels(feature_collection: dict):
    """
    Endpoint to resolve parcel overlaps from a GeoJSON FeatureCollection.

    Args:
        feature_collection (dict): A GeoJSON FeatureCollection object."""
    
    try:
        parcels = parse_feature_collection(feature_collection)
        overlaps = find_overlaps(parcels)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GeoJSON: {error}",
        ) from error

    results = []

    for parcel_a, parcel_b, overlap_area in overlaps:
        results.append(
            {
                "parcel_a": parcel_a,
                "parcel_b": parcel_b,
                "overlap_area": overlap_area,
            }
        )

    return {"overlaps": results}


