from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pyproj.exceptions import CRSError
from shapely.geometry import Polygon

from parcel_resolver.cadastre import validate_parcel
from parcel_resolver.io.geojson import parse_feature_collection
from parcel_resolver.measurement import measure_parcel
from parcel_resolver.projection import reproject_coordinates
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


@app.post("/measure")
async def measure_parcels(feature_collection: dict):
    """
    Endpoint to measure parcel area and perimeter from a GeoJSON
    FeatureCollection.

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
        {"parcel_id": parcel_id, **measure_parcel(coords)}
        for parcel_id, coords in parcels.items()
    ]

    return {"parcels": results}


@app.post("/project")
async def project_parcels(
    feature_collection: dict,
    source_crs: str = Query(..., description='e.g. "EPSG:4326"'),
    target_crs: str = Query(..., description='e.g. "EPSG:3857"'),
):
    """
    Endpoint to reproject parcel coordinates from a GeoJSON FeatureCollection
    between coordinate reference systems.

    Args:
        feature_collection (dict): A GeoJSON FeatureCollection object.
        source_crs (str): The CRS the input coordinates are already in.
        target_crs (str): The CRS to reproject into."""

    try:
        parcels = parse_feature_collection(feature_collection)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GeoJSON: {error}",
        ) from error

    try:
        results = [
            {
                "parcel_id": parcel_id,
                "coordinates": reproject_coordinates(coords, source_crs, target_crs),
            }
            for parcel_id, coords in parcels.items()
        ]
    except CRSError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CRS: {error}",
        ) from error

    return {
        "source_crs": source_crs,
        "target_crs": target_crs,
        "parcels": results,
    }
