from parcel_resolver.resolver.overlap import check_overlap
from tests.fixtures.sample_parcels import SAMPLE_PARCELS

    
    
def test_severity_classification_dispute():
    # P002/P003 overlap area is 9.0, above the tolerance threshold of 5
    result = check_overlap(SAMPLE_PARCELS["P002"], SAMPLE_PARCELS["P003"])
    assert result["severity"] == "dispute"


def test_severity_classification_tolerance():
    # A thin sliver overlapping P002 by area 3.0 -- under the tolerance threshold of 5
    sliver_parcel = [(9.7, 0), (10.3, 0), (10.3, 10), (9.7, 10)]
    result = check_overlap(SAMPLE_PARCELS["P002"], sliver_parcel)
    assert result["severity"] == "tolerance"


def test_severity_classification_none():
    # P001/P002 only share an edge -- zero overlap area
    result = check_overlap(SAMPLE_PARCELS["P001"], SAMPLE_PARCELS["P002"])
    assert result["severity"] == "none"