import io
import zipfile

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
                "severity": "tolerance",
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


def test_validate_returns_structured_results_per_parcel():
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
                "properties": {"parcelid": "P005"},
                "geometry": {
                    "type": "Polygon",
                    # self-intersecting "bowtie"
                    "coordinates": [
                        [[0, 0], [10, 10], [10, 0], [0, 10], [0, 0]]
                    ],
                },
            },
        ],
    }

    response = client.post("/validate", json=feature_collection)

    assert response.status_code == 200
    assert response.json() == {
        "parcels": [
            {
                "parcel_id": "P001",
                "is_valid": True,
                "area": 100.0,
                "flags": [],
            },
            {
                "parcel_id": "P005",
                "is_valid": False,
                "area": 0.0,
                "flags": ["self intersecting", "suspicious area"],
            },
        ]
    }


def test_validate_rejects_feature_collection_without_features():
    response = client.post(
        "/validate",
        json={"type": "FeatureCollection"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid GeoJSON: 'features'",
    }


def test_measure_returns_area_and_perimeter_per_parcel():
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
        ],
    }

    response = client.post("/measure", json=feature_collection)

    assert response.status_code == 200
    assert response.json() == {
        "parcels": [
            {"parcel_id": "P001", "area": 100.0, "perimeter": 40.0},
        ]
    }


def test_measure_rejects_feature_collection_without_features():
    response = client.post(
        "/measure",
        json={"type": "FeatureCollection"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid GeoJSON: 'features'",
    }


def test_project_reprojects_parcel_coordinates():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"parcelid": "P001"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
        ],
    }

    response = client.post(
        "/project",
        params={"source_crs": "EPSG:4326", "target_crs": "EPSG:4326"},
        json=feature_collection,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_crs"] == "EPSG:4326"
    assert body["target_crs"] == "EPSG:4326"
    assert body["parcels"] == [
        {
            "parcel_id": "P001",
            "coordinates": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
        },
    ]


def test_project_rejects_feature_collection_without_features():
    response = client.post(
        "/project",
        params={"source_crs": "EPSG:4326", "target_crs": "EPSG:3857"},
        json={"type": "FeatureCollection"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid GeoJSON: 'features'",
    }


def test_project_rejects_unknown_crs():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"parcelid": "P001"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
        ],
    }

    response = client.post(
        "/project",
        params={"source_crs": "NOT_A_CRS", "target_crs": "EPSG:3857"},
        json=feature_collection,
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid CRS:")


def test_convert_returns_a_zipped_shapefile():
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
        ],
    }

    response = client.post("/convert", json=feature_collection)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "parcels.zip" in response.headers["content-disposition"]

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {
            "parcels.shp",
            "parcels.shx",
            "parcels.dbf",
        }


def test_convert_includes_prj_when_crs_given():
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
        ],
    }

    response = client.post(
        "/convert",
        params={"crs": "EPSG:4326"},
        json=feature_collection,
    )

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "parcels.prj" in archive.namelist()


def test_convert_rejects_feature_collection_without_features():
    response = client.post(
        "/convert",
        json={"type": "FeatureCollection"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid GeoJSON: 'features'",
    }


def test_convert_rejects_unknown_crs():
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
        ],
    }

    response = client.post(
        "/convert",
        params={"crs": "NOT_A_CRS"},
        json=feature_collection,
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid CRS:")
