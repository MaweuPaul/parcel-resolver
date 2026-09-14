import pytest

from parcel_resolver.resolver.overlap import check_overlap
from tests.fixtures.sample_parcels import SAMPLE_PARCELS

    
    
def test_check_overlap_detects_overlapping_parcels():
    # P002/P003 overlap by area 9.0
    result = check_overlap(SAMPLE_PARCELS["P002"], SAMPLE_PARCELS["P003"])
    assert result["overlap"] is True
    assert result["overlap_area"] == 9.0


def test_check_overlap_detects_partial_overlap():
    # A thin sliver overlapping P002 by area 3.0
    sliver_parcel = [(9.7, 0), (10.3, 0), (10.3, 10), (9.7, 10)]
    result = check_overlap(SAMPLE_PARCELS["P002"], sliver_parcel)
    assert result["overlap"] is True
    assert result["overlap_area"] == pytest.approx(3.0)


def test_check_overlap_treats_shared_edge_as_no_overlap():
    # P001/P002 only share an edge -- zero overlap area
    result = check_overlap(SAMPLE_PARCELS["P001"], SAMPLE_PARCELS["P002"])
    assert result["overlap"] is False
    assert result["overlap_area"] == 0.0