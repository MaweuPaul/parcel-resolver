from parcel_resolver.measurement import measure_parcel
from tests.fixtures.sample_parcels import SAMPLE_PARCELS


def test_measure_square_parcel():
    result = measure_parcel(SAMPLE_PARCELS["P001"])

    assert result == {"area": 100.0, "perimeter": 40.0}


def test_measure_tiny_parcel():
    result = measure_parcel(SAMPLE_PARCELS["P006"])

    assert result == {"area": 0.25, "perimeter": 2.0}
