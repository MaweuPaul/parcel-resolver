import pytest

from parcel_resolver.projection import reproject_coordinates


def test_reproject_identity_returns_original_coordinates():
    coords = [(-122.4194, 37.7749), (-122.41, 37.78)]

    result = reproject_coordinates(coords, "EPSG:4326", "EPSG:4326")

    assert result == pytest.approx(coords)


def test_reproject_wgs84_to_web_mercator():
    coords = [(-122.4194, 37.7749)]

    result = reproject_coordinates(coords, "EPSG:4326", "EPSG:3857")

    assert result[0] == pytest.approx((-13627665.27, 4547675.35), rel=1e-6)


def test_reproject_preserves_relative_shape():
    # A 1x1 square near the equator in WGS84 should still be a (roughly)
    # equal-sided square once reprojected into Web Mercator.
    coords = [(0, 0), (1, 0), (1, 1), (0, 1)]

    result = reproject_coordinates(coords, "EPSG:4326", "EPSG:3857")

    width = result[1][0] - result[0][0]
    height = result[2][1] - result[1][1]
    assert width == pytest.approx(height, rel=0.05)
