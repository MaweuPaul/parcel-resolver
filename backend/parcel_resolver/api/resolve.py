from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from shapely.geometry import Polygon

from parcel_resolver.cadastre import validate_parcel
from parcel_resolver.io.geojson import parse_feature_collection
from parcel_resolver.resolver.index import find_overlaps
from parcel_resolver.resolver.severity import classify_severity

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

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
        severity = classify_severity(
            overlap_area,
            Polygon(parcels[parcel_a]).area,
            Polygon(parcels[parcel_b]).area,
        )

        results.append(
            {
                "parcel_a": parcel_a,
                "parcel_b": parcel_b,
                "overlap_area": overlap_area,
                "overlap_percentage": severity["overlap_percentage"],
                "severity": severity["severity"],
            }
        )

    return {"overlaps": results}


@app.post("/validate")
async def validate_parcels(feature_collection: dict):
    """
    Endpoint to validate parcel geometry from a GeoJSON FeatureCollection.

    Args:
        feature_collection (dict): A GeoJSON FeatureCollection object."""

    try:
        parcels = parse_feature_collection(feature_collection)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GeoJSON: {error}",
        ) from error

    results = [
        {"parcel_id": parcel_id, **validate_parcel(coords)}
        for parcel_id, coords in parcels.items()
    ]

    return {"parcels": results}

