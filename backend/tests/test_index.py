from parcel_resolver.resolver.index import find_overlaps
from tests.fixtures.sample_parcels import SAMPLE_PARCELS


def test_find_overlaps_returns_expected_pairs():
    overlaps = find_overlaps(SAMPLE_PARCELS)
    overlap_pairs = [(a, b) for a, b, area in overlaps]

    assert ("P002", "P003") in overlap_pairs
    assert ("P001", "P005") not in overlap_pairs  