from fastapi.testclient import TestClient

from parcel_resolver.api.resolve import app


client = TestClient(app)


def test_resolve_returns_structured_overlap_results():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"parcelid": "P001"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"parcelid": "P002"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[8, 8], [18, 8], [18, 18], [8, 18], [8, 8]]
                    ],
                },
            },
        ],
    }

    response = client.post("/resolve", json=feature_collection)

    assert response.status_code == 200
    assert response.json() == {
        "overlaps": [
            {
                "parcel_a": "P001",
                "parcel_b": "P002",
                "overlap_area": 4.0,
                "overlap_percentage": 4.0,
                "severity": "medium",
            }
        ]
    }


def test_resolve_rejects_feature_collection_without_features():
    response = client.post(
        "/resolve",
        json={"type": "FeatureCollection"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid GeoJSON: 'features'",
    }
