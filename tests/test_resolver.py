from parcel_resolver.resolver.overlap import check_overlap
from tests.fixtures.sample_parcels import SAMPLE_PARCELS


def test_adjacent_parcels_do_not_overlap():
    result = check_overlap(SAMPLE_PARCELS["P001"], SAMPLE_PARCELS["P002"])
    assert result["overlap"] is False
    assert result["overlap_area"] == 0.0


def test_overlapping_parcels_flagged_with_area():
    result = check_overlap(SAMPLE_PARCELS["P002"], SAMPLE_PARCELS["P003"])
    assert result["overlap"] is True
    assert result["overlap_area"] > 0